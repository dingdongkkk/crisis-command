"""SQLite append-only event store with a write-through projection (decisions 0001, 0005).

Every command runs in one ``BEGIN IMMEDIATE`` transaction: receipt lookup, session
check, domain decision against the stored projection, event append, projection update
and receipt save commit together or not at all. Listeners run only after commit.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.contracts import EVENT_ADAPTER
from app.contracts.common import SCHEMA_VERSION
from app.contracts.enums import DispatchState
from app.contracts.events import EVENT_CATALOG, EnvelopeBase, SimulatedDispatchEndedPayload
from app.contracts.state import StateSnapshot
from app.domain.commands import DomainError, NewEvent, session_started
from app.domain.projection import apply, fold

RESET_SCOPE = "*"
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY, fixture TEXT NOT NULL, seed INTEGER NOT NULL,
    ordinal INTEGER NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS events (
    session_id TEXT NOT NULL, sequence INTEGER NOT NULL, event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL, affects_planning INTEGER NOT NULL, idempotency_key TEXT,
    envelope TEXT NOT NULL, PRIMARY KEY (session_id, sequence)
);
CREATE UNIQUE INDEX IF NOT EXISTS events_effect
    ON events (session_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE TABLE IF NOT EXISTS projections (
    session_id TEXT PRIMARY KEY, as_of_sequence INTEGER NOT NULL, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS receipts (
    scope TEXT NOT NULL, method TEXT NOT NULL, path TEXT NOT NULL, idem_key TEXT NOT NULL,
    request_hash TEXT NOT NULL, status INTEGER NOT NULL, body TEXT NOT NULL,
    PRIMARY KEY (scope, method, path, idem_key)
);
"""


class DatabaseBusyError(Exception):
    """The writer lock was not obtained within the busy budget (503, retry same key)."""


@dataclass(frozen=True)
class CommandResult:
    status: int
    body: dict[str, Any]
    replayed: bool
    events: tuple[EnvelopeBase, ...] = ()


@dataclass(frozen=True)
class Decision:
    """Domain outcome: events to append and a builder for the success response body."""

    events: list[NewEvent]
    respond: Callable[[list[EnvelopeBase]], tuple[int, dict[str, Any]]]


Decide = Callable[[StateSnapshot], Decision]
Listener = Callable[[list[EnvelopeBase]], None]
Clock = Callable[[], datetime]


def canonical_hash(body: Any) -> str:
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode()).hexdigest()


def problem(error: DomainError) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": f"https://crisis-command.local/problems/{error.code.lower().replace('_', '-')}",
        "title": error.title,
        "status": error.status,
        "code": error.code,
    }
    if error.detail is not None:
        body["detail"] = error.detail
    if error.current is not None:
        body["current"] = error.current
    return body


def _utc_now() -> datetime:
    return datetime.now(UTC)


class EventStore:
    def __init__(
        self, path: str | Path, *, busy_timeout_s: float = 1.0, clock: Clock = _utc_now
    ) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_s = busy_timeout_s
        self.clock = clock
        self._listeners: list[Listener] = []
        self._listener_lock = threading.Lock()
        with closing(self._connect()) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    # --- connections ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=self.busy_timeout_s, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            try:
                conn.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc) or "busy" in str(exc):
                    raise DatabaseBusyError from exc
                raise
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()

    # --- listeners --------------------------------------------------------------------

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        with self._listener_lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            with self._listener_lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe

    def _notify(self, events: list[EnvelopeBase]) -> None:
        with self._listener_lock:
            listeners = list(self._listeners)
        for listener in listeners:
            listener(events)

    # --- reads ------------------------------------------------------------------------

    def active_session(self) -> str | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key='active_session'").fetchone()
        return None if row is None else str(row["value"])

    def state(self, session_id: str | None = None) -> StateSnapshot:
        session_id = session_id or self.active_session()
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT state FROM projections WHERE session_id=?", (session_id,)
            ).fetchone()
        if row is None:
            raise KeyError(session_id)
        return StateSnapshot.model_validate_json(row["state"])

    def events(
        self, session_id: str, after_sequence: int = 0, limit: int | None = None
    ) -> list[EnvelopeBase]:
        query = "SELECT envelope FROM events WHERE session_id=? AND sequence>? ORDER BY sequence"
        params: tuple[Any, ...] = (session_id, after_sequence)
        if limit is not None:
            query += " LIMIT ?"
            params = (*params, limit)
        with closing(self._connect()) as conn:
            rows = conn.execute(query, params).fetchall()
        return [EVENT_ADAPTER.validate_json(r["envelope"]) for r in rows]

    def head_sequence(self, session_id: str) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS head FROM events WHERE session_id=?",
                (session_id,),
            ).fetchone()
        return int(row["head"])

    def has_session(self, session_id: str) -> bool:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
        return row is not None

    def state_at(self, session_id: str, sequence: int) -> StateSnapshot:
        """Replay: fold the session log from sequence 1 without calling any provider."""
        events = [e for e in self.events(session_id) if e.sequence <= sequence]
        if not events or events[-1].sequence != sequence:
            raise KeyError(sequence)
        return fold(events)

    # --- writes -----------------------------------------------------------------------

    def ensure_session(self, fixture: str = "demo-bengaluru-v1", seed: int = 7) -> str:
        """Create the initial session on first start; a restart reuses the stored one."""
        with self._write() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key='active_session'").fetchone()
            if row is not None:
                return str(row["value"])
            session_id, appended = self._start_session(conn, fixture, seed)
        self._notify(appended)
        return session_id

    def execute(
        self,
        *,
        method: str,
        path: str,
        key: str,
        body: dict[str, Any],
        expected_session_id: str,
        decide: Decide,
        actor: dict[str, str],
    ) -> CommandResult:
        request_hash = canonical_hash(body)
        with self._write() as conn:
            replay = self._receipt(conn, expected_session_id, method, path, key, request_hash)
            if replay is not None:
                return replay
            active = self._active(conn)
            if expected_session_id != active:
                result = CommandResult(409, problem(stale_session(active)), False)
                self._save_receipt(
                    conn, expected_session_id, method, path, key, request_hash, result
                )
                return result
            state = self._projection(conn, active)
            try:
                decision = decide(state)
            except DomainError as error:
                result = CommandResult(error.status, problem(error), False)
                self._save_receipt(conn, active, method, path, key, request_hash, result)
                return result
            appended = self._append(conn, state, decision.events, key, actor)
            status, response = decision.respond(appended)
            result = CommandResult(status, response, False, tuple(appended))
            self._save_receipt(conn, active, method, path, key, request_hash, result)
        self._notify(appended)
        return result

    def reset(
        self, *, key: str, body: dict[str, Any], expected_session_id: str, fixture: str, seed: int
    ) -> CommandResult:
        """Database-wide reset receipt: a retried reset returns the same new session."""
        request_hash = canonical_hash(body)
        method, path = "POST", "/demo/reset"
        with self._write() as conn:
            replay = self._receipt(conn, RESET_SCOPE, method, path, key, request_hash)
            if replay is not None:
                return replay
            active = self._active(conn)
            if expected_session_id != active:
                result = CommandResult(409, problem(stale_session(active)), False)
                self._save_receipt(conn, RESET_SCOPE, method, path, key, request_hash, result)
                return result
            cancelled = self._cancel_pending(conn, active, key)
            session_id, started = self._start_session(conn, fixture, seed)
            result = CommandResult(
                200, {"session_id": session_id, "head_sequence": 1}, False, tuple(started)
            )
            self._save_receipt(conn, RESET_SCOPE, method, path, key, request_hash, result)
        self._notify([*cancelled, *started])
        return result

    # --- internals --------------------------------------------------------------------

    def _active(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT value FROM meta WHERE key='active_session'").fetchone()
        if row is None:
            raise RuntimeError("no active session; call ensure_session() at startup")
        return str(row["value"])

    def _projection(self, conn: sqlite3.Connection, session_id: str) -> StateSnapshot:
        row = conn.execute(
            "SELECT state FROM projections WHERE session_id=?", (session_id,)
        ).fetchone()
        return StateSnapshot.model_validate_json(row["state"])

    def _receipt(
        self, conn: sqlite3.Connection, scope: str, method: str, path: str, key: str, digest: str
    ) -> CommandResult | None:
        row = conn.execute(
            "SELECT request_hash, status, body FROM receipts "
            "WHERE scope=? AND method=? AND path=? AND idem_key=?",
            (scope, method, path, key),
        ).fetchone()
        if row is None:
            return None
        if row["request_hash"] != digest:
            error = DomainError(
                422, "IDEMPOTENCY_KEY_REUSED", "Idempotency key reused with a different request"
            )
            return CommandResult(422, problem(error), False)
        return CommandResult(int(row["status"]), json.loads(row["body"]), True)

    def _save_receipt(
        self,
        conn: sqlite3.Connection,
        scope: str,
        method: str,
        path: str,
        key: str,
        digest: str,
        result: CommandResult,
    ) -> None:
        conn.execute(
            "INSERT INTO receipts (scope, method, path, idem_key, request_hash, status, body) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (scope, method, path, key, digest, result.status, json.dumps(result.body)),
        )

    def _append(
        self,
        conn: sqlite3.Connection,
        state: StateSnapshot | None,
        new_events: list[NewEvent],
        key: str | None,
        actor: dict[str, str],
        session_id: str | None = None,
    ) -> list[EnvelopeBase]:
        session_id = session_id or (state.session_id if state else None)
        if session_id is None:
            raise RuntimeError("append needs a session")
        sequence = state.as_of_sequence if state else 0
        correlation = f"cmd:{key}" if key else f"sys:{uuid.uuid4().hex[:12]}"
        now = self.clock().astimezone(UTC)
        occurred = f"{now:%Y-%m-%dT%H:%M:%S}.{now.microsecond // 1000:03d}Z"
        appended: list[EnvelopeBase] = []
        causation: str | None = None
        for index, new in enumerate(new_events):
            sequence += 1
            event_id = str(uuid.uuid4())
            envelope = EVENT_ADAPTER.validate_python(
                {
                    "schema_version": SCHEMA_VERSION,
                    "event_id": event_id,
                    "session_id": session_id,
                    "sequence": sequence,
                    "event_type": new.event_type,
                    "aggregate_type": new.aggregate_type,
                    "aggregate_id": new.aggregate_id,
                    "occurred_at": occurred,
                    "sim_time_s": new.sim_time_s,
                    "actor": actor,
                    "correlation_id": correlation,
                    "causation_id": causation,
                    "idempotency_key": (key if index == 0 else f"{key}#{index}") if key else None,
                    "affects_planning": _affects(new.event_type),
                    "payload": new.payload.model_dump(mode="json", by_alias=True),
                }
            )
            state = apply(state, envelope)
            conn.execute(
                "INSERT INTO events (session_id, sequence, event_id, event_type, "
                "affects_planning, idempotency_key, envelope) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    sequence,
                    event_id,
                    new.event_type,
                    int(envelope.affects_planning),
                    envelope.idempotency_key,
                    envelope.model_dump_json(by_alias=True),
                ),
            )
            appended.append(envelope)
            causation = event_id
        if state is not None and appended:
            conn.execute(
                "INSERT INTO projections (session_id, as_of_sequence, state) VALUES (?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET as_of_sequence=excluded.as_of_sequence, "
                "state=excluded.state",
                (session_id, state.as_of_sequence, state.model_dump_json(by_alias=True)),
            )
        return appended

    def _start_session(
        self, conn: sqlite3.Connection, fixture: str, seed: int
    ) -> tuple[str, list[EnvelopeBase]]:
        ordinal = int(
            conn.execute("SELECT COALESCE(MAX(ordinal), 0) + 1 AS n FROM sessions").fetchone()["n"]
        )
        session_id = f"sess_{ordinal:04d}"
        conn.execute(
            "INSERT INTO sessions (session_id, fixture, seed, ordinal) VALUES (?, ?, ?, ?)",
            (session_id, fixture, seed, ordinal),
        )
        started = self._append(
            conn,
            None,
            [session_started(session_id, fixture, seed)],
            f"session:{session_id}",
            {"kind": "system", "id": "simulation"},
            session_id=session_id,
        )
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('active_session', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (session_id,),
        )
        return session_id, started

    def _cancel_pending(
        self, conn: sqlite3.Connection, session_id: str, key: str
    ) -> list[EnvelopeBase]:
        state = self._projection(conn, session_id)
        pending = [c for c in state.outbox if c.state is DispatchState.PENDING]
        cancellations = [
            NewEvent(
                "SimulatedDispatchCancelled",
                "dispatch",
                c.outbox_key,
                SimulatedDispatchEndedPayload(outbox_key=c.outbox_key, reason="SESSION_RESET"),
                state.sim_time_s,
            )
            for c in pending
        ]
        if not cancellations:
            return []
        return self._append(
            conn, state, cancellations, f"reset:{key}", {"kind": "system", "id": "simulation"}
        )


def _affects(event_type: str) -> bool:
    return EVENT_CATALOG[event_type][0]


def stale_session(active: str) -> DomainError:
    return DomainError(
        409,
        "STALE_SESSION",
        "Simulation session has changed",
        "The request targets a session that is no longer active; nothing was applied.",
        {"session_id": active},
    )
