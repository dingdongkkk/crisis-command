"""0004 override conflicts: each structural refusal carries a coded reason (CC-11 F2)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.event_store import EventStore
from tests.test_allocation import FixedRoutes
from tests.test_planning_flow import post


@pytest.fixture
def demo(store: EventStore) -> Any:
    """T+10 with every step approved and delivered: A1 on scene, A2 broken down."""
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        sid = store.active_session()
        for step in ("T+0", "T+2", "T+5", "T+10"):
            assert (
                post(
                    client, "/demo/advance", dict(expected_session_id=sid, to_step=step)
                ).status_code
                == 200
            )
            app.state.planner.recompute()
            plan = store.state().current_proposal
            if plan:
                body = dict(
                    expected_session_id=sid,
                    expected_plan_version=plan.version,
                    expected_planning_sequence=plan.based_on_planning_sequence,
                    acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
                )
                assert post(client, f"/plans/{plan.plan_id}/approve", body).status_code == 200
                app.state.planner.deliver()
        app.state.planner.recompute()
        yield client, store


def _override(client: TestClient, store: EventStore, **fields: Any) -> Any:
    state = store.state()
    plan = state.current_proposal or state.approved_plan
    assert plan is not None
    body = dict(
        expected_session_id=state.session_id,
        expected_plan_id=plan.plan_id,
        expected_planning_sequence=state.planning_sequence,
        reason_text="operator test",
        **fields,
    )
    return post(client, "/overrides", body)


def _codes(response: Any) -> list[str]:
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["code"] == "OVERRIDE_CONFLICT"
    return [c["code"] for c in body["conflicts"]]


def _need(store: EventStore, kind: str, exclude_incident: str | None = None) -> Any:
    return next(
        n
        for i in store.state().incidents
        if i.status == "active" and i.incident_id != exclude_incident
        for n in i.needs
        if n.type == kind
    )


def test_bls_pinned_to_als_is_type_ineligible_with_bridge_hint(demo: Any) -> None:
    client, store = demo
    response = _override(
        client, store, kind="pin", unit_id="unit_B2", need_id=_need(store, "als").need_id
    )
    assert _codes(response) == ["TYPE_INELIGIBLE"]
    assert "approve_bls_bridge" in response.json()["conflicts"][0]["detail"]


def test_on_scene_unit_cannot_be_pinned_elsewhere(demo: Any) -> None:
    client, store = demo
    a1 = next(u for u in store.state().units if u.unit_id == "unit_A1")
    assert a1.status == "on_scene"
    task = next(a for a in store.state().approved_plan.assignments if a.unit_id == "unit_A1")
    other = _need(store, "als", exclude_incident=task.incident_id)
    codes = _codes(_override(client, store, kind="pin", unit_id="unit_A1", need_id=other.need_id))
    assert "UNIT_LOCKED" in codes


def test_broken_unit_is_not_available(demo: Any) -> None:
    client, store = demo
    codes = _codes(
        _override(client, store, kind="pin", unit_id="unit_A2", need_id=_need(store, "als").need_id)
    )
    assert codes == ["UNIT_NOT_AVAILABLE"]


def test_hold_then_pin_is_a_duplicate_unit_pin_and_rejection_is_recorded(demo: Any) -> None:
    client, store = demo
    assert _override(client, store, kind="hold_unit", unit_id="unit_B3").status_code == 200
    response = _override(
        client, store, kind="pin", unit_id="unit_B3", need_id=_need(store, "bls").need_id
    )
    assert _codes(response) == ["DUPLICATE_UNIT_PIN"]
    rejected = [
        e
        for e in store.events(store.active_session() or "", 0, 500)
        if e.event_type == "OverrideRejected"
    ]
    recorded = rejected[-1].payload.model_dump(mode="json")["conflicts"]
    assert recorded == response.json()["conflicts"]


def test_pin_against_a_forbid_contradicts_it(demo: Any) -> None:
    client, store = demo
    need = _need(store, "bls")
    incident = next(
        i for i in store.state().incidents if any(n.need_id == need.need_id for n in i.needs)
    )
    assert (
        _override(
            client, store, kind="forbid", unit_id="unit_B3", incident_id=incident.incident_id
        ).status_code
        == 200
    )
    assert _codes(
        _override(client, store, kind="pin", unit_id="unit_B3", need_id=need.need_id)
    ) == ["CONTRADICTS_OVERRIDE"]


def test_water_rescue_pin_reports_route_unavailable(demo: Any) -> None:
    client, store = demo
    codes = _codes(
        _override(
            client,
            store,
            kind="pin",
            unit_id="unit_BT1",
            need_id=_need(store, "water_rescue").need_id,
        )
    )
    assert codes == ["ROUTE_UNAVAILABLE"]


def test_valid_bls_bridge_is_still_accepted(demo: Any) -> None:
    client, store = demo
    als = _need(store, "als")
    response = _override(
        client, store, kind="approve_bls_bridge", unit_id="unit_B3", bridges_need_id=als.need_id
    )
    assert response.status_code == 200, response.text


def test_unmet_reasons_distinguish_water_access_and_unreachable(store: EventStore) -> None:
    """CC-11 F4: "no route" and "water access not modelled" are not "no capacity"."""
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:  # real offline road graph
        sid = store.active_session()
        for text, where in (
            ("Our car is stuck in flood water, water rising, 2 people inside", [77.6200, 12.9700]),
            ("Man collapsed, not breathing", [77.6691, 12.94019]),  # Bellandur lake: no road
        ):
            body = dict(
                expected_session_id=sid,
                channel="text_sim",
                text=text,
                location={"type": "Point", "coordinates": where},
                location_source="fixture",
                sim_time_s=0,
            )
            assert post(client, "/reports", body).status_code == 201
        app.state.planner.recompute()
        plan = store.state().current_proposal
        assert plan is not None
        reasons = {n.type.value: [r.code for r in n.reasons] for n in plan.unmet_needs}
        assert reasons["water_rescue"] == ["WATER_ACCESS_NOT_MODELLED"]
        assert reasons["als"] == ["NO_REACHABLE_UNIT"]


def test_gate_uses_the_allocators_current_route_lock(store: EventStore) -> None:
    """CC-11 F7: a unit that has closed to near arrival since approval is locked by the gate
    too, not only by the allocator (which judges the current route)."""
    from app.domain.commands import DomainError
    from app.planning.allocator import validate_capacity_and_locks

    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes(300)  # approved ETA 300 s: not locked
        sid = store.active_session()
        assert (
            post(client, "/demo/advance", dict(expected_session_id=sid, to_step="T+0")).status_code
            == 200
        )
        app.state.planner.recompute()
        plan = store.state().current_proposal
        assert plan is not None
        body = dict(
            expected_session_id=sid,
            expected_plan_version=plan.version,
            expected_planning_sequence=plan.based_on_planning_sequence,
            acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
        )
        assert post(client, f"/plans/{plan.plan_id}/approve", body).status_code == 200
        app.state.planner.deliver()
        state = store.state()
        approved = state.approved_plan
        assert approved is not None
        moving = next(a for a in approved.assignments if a.eta_s > 120)
        assert next(u for u in state.units if u.unit_id == moving.unit_id).status == "en_route"
        dropped = approved.model_copy(
            update={"assignments": [a for a in approved.assignments if a.unit_id != moving.unit_id]}
        )

        def violations(routes: FixedRoutes) -> str:
            try:
                validate_capacity_and_locks(state, dropped, routes)
            except DomainError as exc:
                return exc.title
            return ""

        assert "LOCK_VIOLATION" not in violations(FixedRoutes(300))
        assert "LOCK_VIOLATION" in violations(FixedRoutes(60))  # now 60 s out: near arrival
