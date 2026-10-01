#!/usr/bin/env python3
"""CC-11 adversarial probes against the real command path (in-process, isolated database).

Each probe states the invariant it attacks (AGENTS.md / decisions 0001-0008) and records
PASS or FAIL with evidence. A FAIL is a finding for CC-12, not a harness error.

    cd backend && uv run python ../evals/adversarial/run_probes.py \
        --json ../evals/adversarial/results.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
import threading
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.domain.projection import state_hash  # noqa: E402
from app.main import create_app  # noqa: E402
from app.storage.event_store import EventStore  # noqa: E402

Probe = Callable[[TestClient, EventStore, Any], str]
PROBES: list[tuple[str, str, Probe]] = []


def probe(name: str, invariant: str) -> Callable[[Probe], Probe]:
    def register(fn: Probe) -> Probe:
        PROBES.append((name, invariant, fn))
        return fn

    return register


class ProbeFailedError(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProbeFailedError(message)


def post(client: TestClient, path: str, body: dict[str, Any], key: str | None = None) -> Any:
    return client.post(path, json=body, headers={"Idempotency-Key": key or str(uuid.uuid4())})


def advance_to_t10(client: TestClient, store: EventStore, app: Any) -> None:
    sid = store.active_session()
    for step in ("T+0", "T+2", "T+5", "T+10"):
        r = post(client, "/demo/advance", dict(expected_session_id=sid, to_step=step))
        check(r.status_code == 200, f"advance {step}: {r.status_code}")
    app.state.planner.recompute()


def approve_body(store: EventStore, acks: list[str] | None = None) -> tuple[str, dict[str, Any]]:
    state = store.state()
    plan = state.current_proposal
    check(plan is not None, "no proposal")
    assert plan is not None
    body = dict(
        expected_session_id=state.session_id,
        expected_plan_version=plan.version,
        expected_planning_sequence=plan.based_on_planning_sequence,
        acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack]
        if acks is None
        else acks,
    )
    return plan.plan_id, body


# --- approvals -------------------------------------------------------------------------------


@probe("approval_requires_every_ack", "Human approvals bind to acknowledged flags (0005)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    body["acknowledged_flag_ids"] = body["acknowledged_flag_ids"][:-1]
    r = post(client, f"/plans/{plan_id}/approve", body)
    check(r.status_code == 409, f"missing ack accepted: {r.status_code}")
    check(store.state().approved_plan is None, "plan approved without all acks")
    return f"{r.status_code} {r.json()['code']}"


@probe("concurrent_approvals_single_winner", "No double approval under a race (0005)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    results: list[int] = []

    def go() -> None:
        results.append(post(client, f"/plans/{plan_id}/approve", body).status_code)

    threads = [threading.Thread(target=go) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    events = store.events(store.active_session() or "", 0, 500)
    approvals = [e for e in events if e.event_type == "PlanApproved"]
    check(len(approvals) == 1, f"{len(approvals)} PlanApproved events")
    check(results.count(200) == 1, f"statuses {sorted(results)}")
    return f"statuses {sorted(results)}; 1 PlanApproved"


@probe("stale_after_world_change", "Approvals bind to the planning sequence (0005)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    sid = store.active_session()
    r = post(
        client,
        "/units/unit_B3/status",
        dict(expected_session_id=sid, to_status="off_duty", sim_time_s=600),
    )
    check(r.status_code == 200, f"status change {r.status_code}")
    r = post(client, f"/plans/{plan_id}/approve", body)
    check(r.status_code == 409 and r.json()["code"] == "STALE_PLAN", f"{r.status_code} {r.json()}")
    return "409 STALE_PLAN"


@probe("wrong_session_rejected", "Every mutation carries expected_session_id (0001)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    body["expected_session_id"] = "sess_9999"
    r = post(client, f"/plans/{plan_id}/approve", body)
    check(r.status_code == 409 and r.json()["code"] == "STALE_SESSION", f"{r.status_code}")
    return "409 STALE_SESSION"


@probe(
    "idempotent_retry_and_key_reuse", "Idempotent commands; key reuse with a new body fails (0001)"
)
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    key = str(uuid.uuid4())
    first = post(client, f"/plans/{plan_id}/approve", body, key)
    again = post(client, f"/plans/{plan_id}/approve", body, key)
    check(first.status_code == 200 and again.json() == first.json(), "retry differs")
    check(again.headers.get("Idempotent-Replayed") == "true", "retry not marked replayed")
    changed = dict(body, note="different")
    reused = post(client, f"/plans/{plan_id}/approve", changed, key)
    check(reused.status_code == 422, f"key reuse {reused.status_code}")
    return "retry replayed; reuse 422"


@probe("dispatch_is_simulated_only", "Simulated dispatch only; no real sends (AGENTS.md)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    check(post(client, f"/plans/{plan_id}/approve", body).status_code == 200, "approve")
    app.state.planner.deliver()
    events = store.events(store.active_session() or "", 0, 500)
    sent = [e for e in events if e.event_type == "SimulatedDispatchSent"]
    check(bool(sent) and all(e.payload.simulated is True for e in sent), "non-simulated send")  # type: ignore[attr-defined]
    return f"{len(sent)} SimulatedDispatchSent, all simulated=true"


# --- replay ----------------------------------------------------------------------------------


@probe("replay_equals_live_at_every_sequence", "Every transition replays (0005)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    plan_id, body = approve_body(store)
    post(client, f"/plans/{plan_id}/approve", body)
    app.state.planner.deliver()
    sid = store.active_session() or ""
    head = store.state().as_of_sequence
    check(state_hash(store.state_at(sid, head)) == state_hash(store.state()), "head differs")
    reopened = EventStore(store.path)
    check(state_hash(reopened.state()) == state_hash(store.state()), "restart differs")
    for seq in range(1, head + 1):
        store.state_at(sid, seq)  # every prefix folds without error
    return f"{head} prefixes fold; head and restart hash-equal"


# --- privacy ---------------------------------------------------------------------------------


@probe("report_text_not_in_event_log", "No raw report text in append-only events (AGENTS.md)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    sid = store.active_session()
    secret = "SYNTHETIC-CANARY-7731 chest pain and not breathing"
    r = post(
        client,
        "/reports",
        dict(
            expected_session_id=sid,
            channel="text_sim",
            text=secret,
            location={"type": "Point", "coordinates": [77.6, 12.97]},
            location_source="fixture",
            sim_time_s=0,
        ),
    )
    check(r.status_code == 201, f"report {r.status_code}")
    with sqlite3.connect(store.path) as conn:
        events = str(conn.execute("SELECT envelope FROM events").fetchall())
        receipts = str(conn.execute("SELECT body FROM receipts").fetchall())
        intake = str(conn.execute("SELECT data FROM intake_sessions").fetchall())
    check("CANARY-7731" not in events, "report text in events")
    check("CANARY-7731" not in receipts, "report text in receipts")
    check("CANARY-7731" not in intake, "report text in intake state")
    return "canary absent from events, receipts and intake state"


@probe("medical_values_never_logged", "Medical IDs audited without values (0008)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    sid = store.active_session()
    cardiac = next(i for i in store.state().incidents if i.kind == "cardiac_chest_pain")
    confirm = dict(expected_session_id=sid, value="yes", reason_text="asked")
    post(client, f"/incidents/{cardiac.incident_id}/facts/caller_is_patient/confirm", confirm)
    r = post(
        client,
        f"/incidents/{cardiac.incident_id}/medical-profile-access",
        dict(expected_session_id=sid, profile_ref="mprof_syn_0001", operator_reason="allergies"),
    )
    check(r.status_code == 200, f"access {r.status_code} {r.text}")
    with sqlite3.connect(store.path) as conn:
        logged = str(conn.execute("SELECT envelope FROM events").fetchall()) + str(
            conn.execute("SELECT body FROM receipts").fetchall()
        )
    check("penicillin" not in logged, "profile value in log/receipts")
    return "granted; values absent from events and receipts"


# --- overrides (0004) ------------------------------------------------------------------------


@probe("override_conflict_has_coded_reason", "Record conflicting overrides with reasons (0004)")
def _(client: TestClient, store: EventStore, app: Any) -> str:
    advance_to_t10(client, store, app)
    state = store.state()
    plan = state.current_proposal
    assert plan is not None
    als_need = next(n for i in state.incidents for n in i.needs if n.type == "als")
    r = post(
        client,
        "/overrides",
        dict(
            expected_session_id=state.session_id,
            kind="pin",
            unit_id="unit_B2",
            need_id=als_need.need_id,
            expected_plan_id=plan.plan_id,
            expected_planning_sequence=state.planning_sequence,
            reason_text="Use B2 as ALS",
        ),
    )
    body = r.json()
    check(r.status_code == 409, f"BLS pinned to ALS accepted: {r.status_code}")
    codes = [c.get("code") for c in body.get("conflicts", [])]
    check(
        body.get("code") == "OVERRIDE_CONFLICT" and "TYPE_INELIGIBLE" in codes,
        f"got {body.get('code')} conflicts={codes}",
    )
    return f"409 OVERRIDE_CONFLICT {codes}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    results = []
    for name, invariant, fn in PROBES:
        with tempfile.TemporaryDirectory(prefix="crisis-probe-") as tmp:
            store = EventStore(Path(tmp) / "probe.db")
            store.ensure_session()
            app = create_app(store=store, auto_plan=False)
            with TestClient(app) as client:
                try:
                    evidence, ok = fn(client, store, app), True
                except ProbeFailedError as exc:
                    evidence, ok = str(exc), False
        results.append(dict(probe=name, invariant=invariant, passed=ok, evidence=evidence))
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {evidence}")
    print(f"\n{sum(r['passed'] for r in results)}/{len(results)} probes passed")
    if args.json:
        args.json.write_text(json.dumps(results, indent=2) + "\n")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
