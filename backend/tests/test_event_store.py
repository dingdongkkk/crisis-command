"""Event store: idempotency, sessions, concurrency, replay and restart (CC-03)."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from app.contracts.commands import UnitStatusCommand
from app.contracts.enums import DispatchAction, DispatchState
from app.contracts.events import SimulatedDispatchQueuedPayload
from app.contracts.state import DispatchCommand, StateSnapshot
from app.domain.commands import DomainError, NewEvent, unit_status
from app.domain.projection import fold, state_hash
from app.storage.event_store import DatabaseBusyError, Decision, EventStore

OP = {"kind": "operator", "id": "op_test"}


def _status(store: EventStore, unit: str, to: str, key: str, session: str | None = None) -> Any:
    session = session or store.active_session() or ""
    command = UnitStatusCommand(to_status=to, sim_time_s=10, expected_session_id=session)
    return store.execute(
        method="POST",
        path=f"/units/{unit}/status",
        key=key,
        body=command.model_dump(mode="json"),
        expected_session_id=session,
        decide=lambda s: Decision(
            [unit_status(s, unit, command)], lambda ev: (200, {"sequence": ev[0].sequence})
        ),
        actor=OP,
    )


def test_initial_session_is_seeded_and_projection_equals_replay(store: EventStore) -> None:
    session = store.active_session()
    assert session == "sess_0001"
    state = store.state()
    assert (state.as_of_sequence, state.planning_sequence) == (1, 1)
    assert len(state.units) == 9 and {f.facility_id for f in state.facilities} >= {
        "hosp_H1",
        "shelter_S2",
    }
    assert all(u.status == "available" for u in state.units)
    assert state_hash(fold(store.events(session))) == state_hash(state)


def test_duplicate_command_appends_once_and_replays_response(store: EventStore) -> None:
    first = _status(store, "unit_A2", "broken_down", "k1")
    again = _status(store, "unit_A2", "broken_down", "k1")
    assert first.status == 200 and not first.replayed
    assert again.replayed and again.body == first.body
    assert store.head_sequence(store.active_session() or "") == 2


def test_key_reuse_with_different_body_is_rejected(store: EventStore) -> None:
    _status(store, "unit_A2", "broken_down", "k1")
    reused = _status(store, "unit_A2", "off_duty", "k1")
    assert reused.status == 422 and reused.body["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert store.head_sequence(store.active_session() or "") == 2


def test_domain_rejection_is_recorded_and_idempotent(store: EventStore) -> None:
    bad = _status(store, "unit_A1", "on_scene", "k2")  # no task: invalid
    assert bad.status == 409 and bad.body["code"] == "INVALID_TRANSITION"
    assert _status(store, "unit_A1", "on_scene", "k2").replayed
    assert store.head_sequence(store.active_session() or "") == 1


def test_stale_session_never_mutates_new_session(store: EventStore) -> None:
    old = store.active_session() or ""
    store.reset(
        key="r1", body={"x": 1}, expected_session_id=old, fixture="demo-bengaluru-v1", seed=7
    )
    new = store.active_session() or ""
    result = _status(store, "unit_A2", "broken_down", "k3", session=old)
    assert result.status == 409 and result.body["code"] == "STALE_SESSION"
    assert store.head_sequence(new) == 1


def test_reset_retry_returns_same_session_even_after_later_resets(store: EventStore) -> None:
    first = store.active_session() or ""
    kwargs: dict[str, Any] = {"fixture": "demo-bengaluru-v1", "seed": 7}
    r1 = store.reset(key="reset-a", body={"a": 1}, expected_session_id=first, **kwargs)
    r2 = store.reset(
        key="reset-b", body={"b": 1}, expected_session_id=r1.body["session_id"], **kwargs
    )
    retry = store.reset(key="reset-a", body={"a": 1}, expected_session_id=first, **kwargs)
    assert retry.replayed and retry.body == r1.body
    assert store.active_session() == r2.body["session_id"] == "sess_0003"
    reused = store.reset(key="reset-a", body={"a": 2}, expected_session_id=first, **kwargs)
    assert reused.status == 422


def test_reset_cancels_pending_simulated_dispatch(store: EventStore) -> None:
    session = store.active_session() or ""
    command = DispatchCommand(
        session_id=session,
        outbox_key=f"{session}:plan_0001:assign:asg_1",
        plan_id="plan_0001",
        action=DispatchAction.ASSIGN,
        unit_id="unit_B1",
        assignment_id="asg_1",
        desired_revision=1,
        state=DispatchState.PENDING,
        simulated=True,
    )
    queued = NewEvent(
        "SimulatedDispatchQueued",
        "dispatch",
        command.outbox_key,
        SimulatedDispatchQueuedPayload(command=command),
        0,
    )
    store.execute(
        method="POST",
        path="/test",
        key="q1",
        body={},
        expected_session_id=session,
        decide=lambda s: Decision([queued], lambda ev: (200, {})),
        actor=OP,
    )
    store.reset(key="r", body={}, expected_session_id=session, fixture="demo-bengaluru-v1", seed=7)
    old = store.state(session)
    assert [c.state for c in old.outbox] == ["cancelled"]
    assert store.events(session)[-1].event_type == "SimulatedDispatchCancelled"


def test_restart_reuses_session_and_state(db_path: Path, store: EventStore) -> None:
    _status(store, "unit_A2", "broken_down", "k1")
    before = state_hash(store.state())
    reopened = EventStore(db_path)
    assert reopened.ensure_session() == store.active_session()
    assert state_hash(reopened.state()) == before
    assert state_hash(fold(reopened.events(reopened.active_session() or ""))) == before


def test_state_at_replays_without_appending(store: EventStore) -> None:
    _status(store, "unit_A2", "broken_down", "k1")
    _status(store, "unit_B1", "off_duty", "k2")
    session = store.active_session() or ""
    at2 = store.state_at(session, 2)
    assert at2.as_of_sequence == 2
    assert next(u for u in at2.units if u.unit_id == "unit_B1").status == "available"
    assert store.head_sequence(session) == 3
    suffix = fold(store.events(session, 2), at2)
    assert state_hash(suffix) == state_hash(store.state())


def test_concurrent_distinct_commands_are_gapless(store: EventStore) -> None:
    units = ["unit_A1", "unit_A2", "unit_B1", "unit_B2", "unit_B3", "unit_F1"]
    threads = [
        threading.Thread(target=_status, args=(store, u, "off_duty", f"c-{u}")) for u in units
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    session = store.active_session() or ""
    assert [e.sequence for e in store.events(session)] == list(range(1, len(units) + 2))


def test_concurrent_version_checks_admit_exactly_one(store: EventStore) -> None:
    session = store.active_session() or ""
    expected = store.state().planning_sequence
    outcomes: list[int] = []

    def guarded(state: StateSnapshot, unit: str) -> Decision:
        if state.planning_sequence != expected:
            raise DomainError(409, "STALE_PLAN", "Plan is no longer current")
        time.sleep(0.1)  # widen the race window while holding the write lock
        command = UnitStatusCommand(to_status="off_duty", sim_time_s=5, expected_session_id=session)
        return Decision([unit_status(state, unit, command)], lambda ev: (200, {}))

    def run(unit: str) -> None:
        result = store.execute(
            method="POST",
            path="/guarded",
            key=f"g-{unit}",
            body={"u": unit},
            expected_session_id=session,
            decide=lambda s: guarded(s, unit),
            actor=OP,
        )
        outcomes.append(result.status)

    threads = [threading.Thread(target=run, args=(u,)) for u in ("unit_A1", "unit_A2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == [200, 409]
    assert store.head_sequence(session) == 2


def test_busy_writer_lock_raises_database_busy(db_path: Path, store: EventStore) -> None:
    quick = EventStore(db_path, busy_timeout_s=0.05)
    blocker = sqlite3.connect(db_path, isolation_level=None)
    blocker.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(DatabaseBusyError):
            _status(quick, "unit_A2", "broken_down", "busy")
    finally:
        blocker.execute("ROLLBACK")
        blocker.close()
    # Nothing was recorded, so the same key succeeds once the lock is free.
    assert _status(quick, "unit_A2", "broken_down", "busy").status == 200
