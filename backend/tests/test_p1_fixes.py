"""CC-12 P1 findings from the Codex whole-code review, each reproduced then fixed."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.contracts.entities import Route
from app.contracts.state import StateSnapshot
from app.main import create_app
from app.storage.event_store import EventStore
from tests.test_allocation import FixedRoutes
from tests.test_planning_flow import post


class FloodAwareRoutes(FixedRoutes):
    """300 s everywhere until any road-closing flood exists, then no route at all."""

    def route(
        self, state: StateSnapshot, origin: tuple[float, float], destination: tuple[float, float]
    ) -> Route:
        self.unavailable = any(f.closes_roads for f in state.flood)
        return super().route(state, origin, destination)


def _report(client: TestClient, sid: str, text: str, at: list[float], t: int = 0) -> Any:
    body = dict(
        expected_session_id=sid,
        channel="text_sim",
        text=text,
        location={"type": "Point", "coordinates": at},
        location_source="fixture",
        sim_time_s=t,
    )
    response = post(client, "/reports", body)
    assert response.status_code == 201, response.text
    return response.json()


def _approve(client: TestClient, store: EventStore) -> None:
    plan = store.state().current_proposal
    assert plan is not None
    body = dict(
        expected_session_id=store.active_session(),
        expected_plan_version=plan.version,
        expected_planning_sequence=plan.based_on_planning_sequence,
        acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
    )
    assert post(client, f"/plans/{plan.plan_id}/approve", body).status_code == 200


def test_flood_after_approval_cancels_queued_dispatch(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FloodAwareRoutes()
        sid = store.active_session() or ""
        _report(client, sid, "Chest pain, not breathing normally", [77.6, 12.97])
        app.state.planner.recompute()
        _approve(client, store)
        assert any(c.state == "pending" for c in store.state().outbox)
        flood = dict(
            expected_session_id=sid,
            flood_id="flood_p1",
            version=1,
            closes_roads=True,
            effective_sim_time_s=0,
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [[77.59, 12.96], [77.61, 12.96], [77.61, 12.98], [77.59, 12.98], [77.59, 12.96]]
                ],
            },
        )
        assert post(client, "/flood-events", flood).status_code == 201
        app.state.planner.deliver()
        events = [e.model_dump(mode="json") for e in store.events(sid, 0, 500)]
        sent = [
            e
            for e in events
            if e["event_type"] == "SimulatedDispatchSent" and e["payload"]["action"] == "assign"
        ]
        assert sent == []
        reasons = {
            e["payload"]["reason"]
            for e in events
            if e["event_type"] == "SimulatedDispatchCancelled"
        }
        assert "ROUTE_INVALIDATED" in reasons
        assert all(u.status != "en_route" for u in store.state().units)


def test_delivery_without_flood_still_sends(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FloodAwareRoutes()
        sid = store.active_session() or ""
        _report(client, sid, "Chest pain, not breathing normally", [77.6, 12.97])
        app.state.planner.recompute()
        _approve(client, store)
        app.state.planner.deliver()
        assert any(u.status == "en_route" for u in store.state().units)


def test_medical_consent_does_not_cross_a_session_reset(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        old = store.active_session() or ""
        created = _report(client, old, "Chest pain, I am the patient", [77.6, 12.97])
        profile = dict(
            expected_session_id=old,
            consent_granted=True,
            scope=["allergies"],
            allergies=["SYNTHETIC_OLD_SESSION"],
            linked_incident_id=created["incident_id"],
            synthetic=True,
        )
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        assert (
            client.put("/medical-profiles/mprof_p1", json=profile, headers=headers).status_code
            == 200
        )
        reset = post(
            client,
            "/demo/reset",
            dict(expected_session_id=old, fixture="demo-bengaluru-v1", seed=7),
        )
        new = reset.json()["session_id"]
        again = _report(client, new, "Chest pain, I am the patient", [77.6, 12.97])
        assert again["incident_id"] == created["incident_id"]  # IDs restart per session
        confirm = dict(expected_session_id=new, value="yes", reason_text="asked")
        assert (
            post(
                client,
                f"/incidents/{again['incident_id']}/facts/caller_is_patient/confirm",
                confirm,
            ).status_code
            == 200
        )
        access = post(
            client,
            f"/incidents/{again['incident_id']}/medical-profile-access",
            dict(expected_session_id=new, profile_ref="mprof_p1", operator_reason="allergy check"),
        )
        assert access.status_code == 403
        assert access.json()["reason"] == "PROFILE_NOT_LINKED"
        assert "SYNTHETIC_OLD_SESSION" not in access.text


def test_confirmed_life_threat_upgrades_an_information_request(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        sid = store.active_session() or ""
        created = _report(client, sid, "Is the Hebbal flyover open?", [77.59, 13.03])
        iid = created["incident_id"]
        before = next(i for i in store.state().incidents if i.incident_id == iid)
        assert before.category == "information_request" and before.needs == []
        confirm = dict(
            expected_session_id=sid, value="no", reason_text="Caller says driver is not breathing"
        )
        assert (
            post(client, f"/incidents/{iid}/facts/breathing_normally/confirm", confirm).status_code
            == 200
        )
        after = next(i for i in store.state().incidents if i.incident_id == iid)
        assert after.category == "emergency"
        assert after.severity == "critical"
        assert "als" in [n.type for n in after.needs]
        kinds = [e.event_type for e in store.events(sid, 0, 500)]
        assert kinds[-2:] == ["IncidentCategoryChanged", "EscalatedToHuman"]
        app.state.planner.recompute()
        plan = store.state().current_proposal
        assert plan is not None
        planned = {a.incident_id for a in plan.assignments} | {
            n.incident_id for n in plan.unmet_needs
        }
        assert iid in planned


def test_linking_a_duplicate_keeps_demand_only_the_second_caller_reported(
    store: EventStore,
) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        sid = store.active_session() or ""
        first = _report(client, sid, "Strong gas smell in the building", [77.6000, 12.9700])
        second = _report(
            client, sid, "Gas leak, a man fainted and is not breathing", [77.6001, 12.9701]
        )
        state = store.state()
        original = next(i for i in state.incidents if i.incident_id == first["incident_id"])
        candidate = next(i for i in state.incidents if i.incident_id == second["incident_id"])
        assert candidate.duplicate_candidate_of == [original.incident_id]
        assert "als" not in [n.type for n in original.needs]
        assert "als" in [n.type for n in candidate.needs]

        body = dict(expected_session_id=sid, resolution="linked", reason_text="Same building")
        path = f"/incidents/{original.incident_id}/duplicates/{second['report_id']}/resolve"
        assert post(client, path, body).status_code == 200
        state = store.state()
        merged = next(i for i in state.incidents if i.incident_id == original.incident_id)
        assert "als" in [n.type for n in merged.needs]
        assert merged.severity == "critical"
        app.state.planner.recompute()
        plan = store.state().current_proposal
        assert plan is not None
        als = f"{original.incident_id}_als"
        assert any(a.need_id == als for a in plan.assignments) or any(
            n.need_id == als for n in plan.unmet_needs
        )
        from app.domain.projection import state_hash

        assert state_hash(store.state_at(sid, state.as_of_sequence)) == state_hash(state)
