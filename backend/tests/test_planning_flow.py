from __future__ import annotations

import uuid
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import cast

from fastapi.testclient import TestClient
from httpx import Response

from app.domain.projection import state_hash
from app.main import create_app
from app.storage.event_store import EventStore
from tests.test_allocation import FixedRoutes


def post(
    client: TestClient, path: str, body: Mapping[str, object], key: str | None = None
) -> Response:
    return cast(
        Response,
        client.post(path, json=body, headers={"Idempotency-Key": key or str(uuid.uuid4())}),
    )


def prepare(client: TestClient, store: EventStore) -> None:
    response = post(
        client,
        "/reports",
        dict(
            expected_session_id=store.active_session(),
            channel="text_sim",
            text="Chest pain; I need a human",
            location={"type": "Point", "coordinates": [77.6, 12.97]},
            location_source="fixture",
            sim_time_s=0,
        ),
    )
    assert response.status_code == 201, response.text


def test_approve_once_replay_and_restart(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as c:
        app.state.planner.routes = FixedRoutes()
        prepare(c, store)
        app.state.planner.recompute()
        state = store.state()
        plan = state.current_proposal
        assert plan
        body = dict(
            expected_session_id=state.session_id,
            expected_plan_version=plan.version,
            expected_planning_sequence=plan.based_on_planning_sequence,
            acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
        )
        key = str(uuid.uuid4())

        def approve_once() -> int:
            return post(c, f"/plans/{plan.plan_id}/approve", body, key).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(lambda _: approve_once(), range(2))) == [200, 200]
        app.state.planner.deliver()
        after = store.state()
        assert after.approved_plan and after.approved_plan.state == "dispatched_simulated"
        seq = after.as_of_sequence
        app.state.planner.deliver()
        assert store.state().as_of_sequence == seq
        assert state_hash(store.state_at(after.session_id, seq)) == state_hash(after)
        reopened = EventStore(store.path)
        assert state_hash(reopened.state()) == state_hash(after)
        assert (
            len(
                [
                    e
                    for e in store.events(after.session_id, 0, 500)
                    if e.event_type == "PlanApproved"
                ]
            )
            == 1
        )


def test_stale_approval_and_breakdown_before_delivery(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as c:
        app.state.planner.routes = FixedRoutes()
        prepare(c, store)
        app.state.planner.recompute()
        s = store.state()
        p = s.current_proposal
        assert p and p.assignments
        body = dict(
            expected_session_id=s.session_id,
            expected_plan_version=p.version,
            expected_planning_sequence=p.based_on_planning_sequence,
            acknowledged_flag_ids=[f.flag_id for f in p.flags if f.requires_ack],
        )
        assert post(c, f"/plans/{p.plan_id}/approve", body).status_code == 200
        unit_id = p.assignments[0].unit_id
        assert (
            post(
                c,
                f"/units/{unit_id}/status",
                dict(expected_session_id=s.session_id, to_status="broken_down", sim_time_s=1),
            ).status_code
            == 200
        )
        app.state.planner.deliver()
        assert next(u for u in store.state().units if u.unit_id == unit_id).status == "broken_down"
        assert all(d.state != "sent" for d in store.state().outbox if d.unit_id == unit_id)
        app.state.planner.recompute()
        assert post(c, f"/plans/{p.plan_id}/approve", body).status_code == 409
        assert any(e.event_type == "ApprovalRejected" for e in store.events(s.session_id, 0, 500))


def test_session_reset_and_missing_acks(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as c:
        app.state.planner.routes = FixedRoutes(unavailable=True)
        prepare(c, store)
        app.state.planner.recompute()
        s = store.state()
        p = s.current_proposal
        assert p
        body = dict(
            expected_session_id=s.session_id,
            expected_plan_version=p.version,
            expected_planning_sequence=p.based_on_planning_sequence,
            acknowledged_flag_ids=[],
        )
        assert post(c, f"/plans/{p.plan_id}/approve", body).json()["code"] == "UNACKNOWLEDGED_FLAGS"
        assert (
            post(
                c,
                "/demo/reset",
                dict(expected_session_id=s.session_id, fixture="demo-bengaluru-v1", seed=7),
            ).status_code
            == 200
        )
        assert post(c, f"/plans/{p.plan_id}/approve", body).json()["code"] == "STALE_SESSION"


def test_repair_does_not_resurrect_pending_assignment(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        prepare(client, store)
        app.state.planner.recompute()
        state = store.state()
        plan = state.current_proposal
        assert plan and plan.assignments
        post(
            client,
            f"/plans/{plan.plan_id}/approve",
            dict(
                expected_session_id=state.session_id,
                expected_plan_version=plan.version,
                expected_planning_sequence=plan.based_on_planning_sequence,
                acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
            ),
        )
        uid = plan.assignments[0].unit_id
        for t, status in ((1, "broken_down"), (2, "available")):
            assert (
                post(
                    client,
                    f"/units/{uid}/status",
                    dict(expected_session_id=state.session_id, to_status=status, sim_time_s=t),
                ).status_code
                == 200
            )
        app.state.planner.deliver()
        assert next(u for u in store.state().units if u.unit_id == uid).current_task is None
        assert all(c.state == "cancelled" for c in store.state().outbox if c.unit_id == uid)


def test_override_conflict_and_valid_downgrade(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        prepare(client, store)
        app.state.planner.recompute()
        state = store.state()
        plan = state.current_proposal
        assert plan and plan.assignments
        need = plan.assignments[0].need_id
        bls = next(u for u in state.units if u.type == "bls")
        body = dict(
            expected_session_id=state.session_id,
            expected_plan_id=plan.plan_id,
            expected_planning_sequence=state.planning_sequence,
            kind="pin",
            unit_id=bls.unit_id,
            need_id=need,
            reason_text="Try incompatible resource",
        )
        result = post(client, "/overrides", body)
        assert result.status_code == 409
        assert store.state().active_overrides == []
        assert any(
            e.event_type == "OverrideRejected" for e in store.events(state.session_id, 0, 500)
        )
