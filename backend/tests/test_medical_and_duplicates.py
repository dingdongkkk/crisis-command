"""Medical ID denial reasons (0008) and operator duplicate resolution (0007 AS-07)."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.event_store import EventStore
from tests.test_allocation import FixedRoutes
from tests.test_planning_flow import post, prepare


def _put_profile(client: TestClient, sid: str, **overrides: Any) -> None:
    body: dict[str, Any] = dict(
        expected_session_id=sid,
        consent_granted=True,
        scope=["allergies", "medications"],
        allergies=["SYNTHETIC_PENICILLIN"],
        medications=["SYNTHETIC_DRUG"],
        synthetic=True,
    )
    body.update(overrides)
    response = client.put(
        "/medical-profiles/mprof_syn_0001",
        json=body,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 200, response.text


def _access(client: TestClient, sid: str, iid: str, reason: str = "Allergy check") -> Any:
    return post(
        client,
        f"/incidents/{iid}/medical-profile-access",
        dict(expected_session_id=sid, profile_ref="mprof_syn_0001", operator_reason=reason),
    )


def _confirm_patient(client: TestClient, sid: str, iid: str, value: str) -> None:
    body = dict(expected_session_id=sid, value=value, reason_text="Asked the caller")
    response = post(client, f"/incidents/{iid}/facts/caller_is_patient/confirm", body)
    assert response.status_code == 200, response.text


@pytest.fixture
def ready(store: EventStore) -> Any:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        prepare(client, store)
        yield client, store.active_session(), store.state().incidents[0].incident_id


def _reason(response: Any) -> str:
    assert response.status_code == 403, response.text
    body = response.json()
    assert body["code"] == "PROFILE_ACCESS_DENIED"
    return str(body["reason"])


def test_every_denial_reason_in_rule_order(ready: Any, store: EventStore) -> None:
    client, sid, iid = ready
    assert _reason(_access(client, sid, iid, reason="   ")) == "MISSING_OPERATOR_REASON"
    assert _reason(_access(client, sid, "incident_404")) == "INCIDENT_NOT_ACTIVE"
    assert _reason(_access(client, sid, iid)) == "PROFILE_NOT_LINKED"  # no profile yet
    _put_profile(client, sid, linked_incident_id=iid, consent_granted=False)
    assert _reason(_access(client, sid, iid)) == "NO_CONSENT"  # never granted
    _put_profile(client, sid, linked_incident_id="incident_other")
    assert _reason(_access(client, sid, iid)) == "PROFILE_NOT_LINKED"
    _put_profile(client, sid, linked_incident_id=iid)
    assert _reason(_access(client, sid, iid)) == "CALLER_IS_PATIENT_UNKNOWN"
    _confirm_patient(client, sid, iid, "unknown")
    assert _reason(_access(client, sid, iid)) == "CALLER_IS_PATIENT_UNKNOWN"
    _confirm_patient(client, sid, iid, "no")
    assert _reason(_access(client, sid, iid)) == "CALLER_IS_NOT_PATIENT"
    _confirm_patient(client, sid, iid, "yes")
    granted = _access(client, sid, iid)
    assert granted.status_code == 200
    assert granted.json()["values"] == {
        "allergies": ["SYNTHETIC_PENICILLIN"],
        "medications": ["SYNTHETIC_DRUG"],
    }
    assert granted.headers["Cache-Control"] == "no-store"
    _put_profile(client, sid, linked_incident_id=iid, consent_granted=False)
    assert _reason(_access(client, sid, iid)) == "CONSENT_REVOKED"

    events = store.events(sid, 0, 500)
    audits = [e for e in events if e.event_type.startswith("MedicalProfileAccess")]
    assert len(audits) == 10
    assert [a.payload.reason for a in audits if a.event_type.endswith("Denied")][:3] == [  # type: ignore[attr-defined]
        "MISSING_OPERATOR_REASON",
        "INCIDENT_NOT_ACTIVE",
        "PROFILE_NOT_LINKED",
    ]
    with sqlite3.connect(store.path) as conn:
        log = str(conn.execute("SELECT envelope FROM events").fetchall())
        receipts = str(conn.execute("SELECT body FROM receipts").fetchall())
    for secret in ("SYNTHETIC_PENICILLIN", "SYNTHETIC_DRUG"):
        assert secret not in log and secret not in receipts


def test_old_access_path_is_gone(ready: Any) -> None:
    client, sid, iid = ready
    response = post(
        client,
        f"/incidents/{iid}/medical-profile/access",
        dict(expected_session_id=sid, profile_ref="mprof_syn_0001", operator_reason="x"),
    )
    assert response.status_code in (404, 405)


def test_operator_confirmation_survives_intake_answers(ready: Any, store: EventStore) -> None:
    client, sid, _ = ready
    created = post(
        client,
        "/reports",
        dict(
            expected_session_id=sid,
            channel="text_sim",
            text="someone fell down near the bus stop",
            location={"type": "Point", "coordinates": [77.61, 12.95]},
            location_source="fixture",
            sim_time_s=0,
        ),
    ).json()
    iid, report_id = created["incident_id"], created["report_id"]
    _confirm_patient(client, sid, iid, "yes")
    facts = next(f for f in store.state().triage_facts if f.incident_id == iid)
    pending = facts.questions_asked[-1]
    assert pending.answer is None
    body = dict(expected_session_id=sid, fact_key=pending.fact_key, answer="unknown")
    assert post(client, f"/reports/{report_id}/answers", body).status_code == 200
    facts = next(f for f in store.state().triage_facts if f.incident_id == iid)
    patient = next(f for f in facts.facts if f.key == "caller_is_patient")
    assert patient.value == "yes" and patient.confirmed_by_operator


# --- duplicates ------------------------------------------------------------------------------


def _to_t5(client: TestClient, store: EventStore) -> str:
    sid = store.active_session()
    assert sid
    for step in ("T+0", "T+2", "T+5"):
        response = post(client, "/demo/advance", dict(expected_session_id=sid, to_step=step))
        assert response.status_code == 200, response.text
    return sid


@pytest.fixture
def at_t5(store: EventStore) -> Any:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        sid = _to_t5(client, store)
        app.state.planner.recompute()
        state = store.state()
        candidate = next(i for i in state.incidents if i.duplicate_candidate_of)
        yield client, app, sid, candidate


def _flags(store: EventStore) -> list[Any]:
    plan = store.state().current_proposal
    assert plan is not None
    return [f for f in plan.flags if f.code == "DUPLICATE_CANDIDATE_UNRESOLVED"]


def test_duplicate_candidate_is_flagged_for_acknowledgement(at_t5: Any, store: EventStore) -> None:
    _, _, _, candidate = at_t5
    flags = _flags(store)
    assert [f.incident_id for f in flags] == [candidate.incident_id]
    assert flags[0].requires_ack and flags[0].severity == "warning"


def test_linking_merges_the_candidate_and_removes_double_counted_needs(
    at_t5: Any, store: EventStore
) -> None:
    client, app, sid, candidate = at_t5
    original = candidate.duplicate_candidate_of[0]
    report_id = candidate.report_ids[0]
    body = dict(expected_session_id=sid, resolution="linked", reason_text="Same vehicle")
    response = post(client, f"/incidents/{original}/duplicates/{report_id}/resolve", body)
    assert response.status_code == 200, response.text
    assert response.json()["candidate_incident_id"] == candidate.incident_id
    app.state.planner.recompute()
    state = store.state()
    merged = next(i for i in state.incidents if i.incident_id == candidate.incident_id)
    assert merged.status == "merged_duplicate"
    assert report_id in next(i for i in state.incidents if i.incident_id == original).report_ids
    assert next(r for r in state.reports if r.report_id == report_id).linked_incident_id == original
    plan = state.current_proposal
    assert plan is not None
    assert all(n.incident_id != candidate.incident_id for n in plan.unmet_needs)
    assert all(a.incident_id != candidate.incident_id for a in plan.assignments)
    assert _flags(store) == []


def test_keeping_separate_clears_the_flag_and_keeps_both(at_t5: Any, store: EventStore) -> None:
    client, app, sid, candidate = at_t5
    original = candidate.duplicate_candidate_of[0]
    body = dict(expected_session_id=sid, resolution="kept_separate", reason_text="Two cars")
    path = f"/incidents/{original}/duplicates/{candidate.report_ids[0]}/resolve"
    assert post(client, path, body).status_code == 200
    app.state.planner.recompute()
    state = store.state()
    kept = next(i for i in state.incidents if i.incident_id == candidate.incident_id)
    assert kept.status == "active" and kept.duplicate_candidate_of == []
    assert _flags(store) == []
    again = post(client, path, body)
    assert again.status_code == 409 and again.json()["code"] == "NOT_A_DUPLICATE_CANDIDATE"


def test_resolution_replays_to_the_same_state(at_t5: Any, store: EventStore) -> None:
    from app.domain.projection import state_hash

    client, _, sid, candidate = at_t5
    original = candidate.duplicate_candidate_of[0]
    body = dict(expected_session_id=sid, resolution="linked", reason_text="Same vehicle")
    post(client, f"/incidents/{original}/duplicates/{candidate.report_ids[0]}/resolve", body)
    state = store.state()
    assert state_hash(store.state_at(sid, state.as_of_sequence)) == state_hash(state)


def test_demo_seeds_a_consented_synthetic_profile_for_the_t0_cardiac_caller(
    store: EventStore,
) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        sid = store.active_session()
        assert sid
        assert (
            post(client, "/demo/advance", dict(expected_session_id=sid, to_step="T+0")).status_code
            == 200
        )
        cardiac = next(i for i in store.state().incidents if i.kind == "cardiac_chest_pain")
        assert _reason(_access(client, sid, cardiac.incident_id)) == "CALLER_IS_PATIENT_UNKNOWN"
        _confirm_patient(client, sid, cardiac.incident_id, "yes")
        granted = _access(client, sid, cardiac.incident_id)
        assert granted.status_code == 200, granted.text
        assert granted.json()["values"]["allergies"] == ["SYNTHETIC: penicillin"]
