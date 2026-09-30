from __future__ import annotations

import sqlite3
import uuid

from fastapi.testclient import TestClient

from app.domain.projection import state_hash
from app.main import create_app
from app.storage.event_store import EventStore
from tests.test_allocation import FixedRoutes
from tests.test_planning_flow import post, prepare


def test_consent_revocation_and_no_values_in_log_receipts(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        prepare(client, store)
        sid = store.active_session()
        iid = store.state().incidents[0].incident_id
        write = dict(
            expected_session_id=sid,
            consent_granted=True,
            scope=["allergies"],
            allergies=["SYNTHETIC_SECRET"],
            synthetic=True,
        )
        assert (
            client.put(
                "/medical-profiles/profile_demo",
                json=write,
                headers={"Idempotency-Key": str(uuid.uuid4())},
            ).status_code
            == 200
        )
        access = dict(
            expected_session_id=sid,
            profile_ref="profile_demo",
            caller_is_patient=False,
            operator_reason="Synthetic demo",
        )
        assert post(client, f"/incidents/{iid}/medical-profile/access", access).status_code == 403
        access["caller_is_patient"] = True
        key = str(uuid.uuid4())
        result = post(client, f"/incidents/{iid}/medical-profile/access", access, key)
        assert result.status_code == 200
        assert result.json()["values"] == {"allergies": ["SYNTHETIC_SECRET"]}
        write["consent_granted"] = False
        assert (
            client.put(
                "/medical-profiles/profile_demo",
                json=write,
                headers={"Idempotency-Key": str(uuid.uuid4())},
            ).status_code
            == 200
        )
        assert (
            post(client, f"/incidents/{iid}/medical-profile/access", access, key).status_code == 403
        )
        with sqlite3.connect(store.path) as conn:
            assert "SYNTHETIC_SECRET" not in str(
                conn.execute("SELECT envelope FROM events").fetchall()
            )
            assert "SYNTHETIC_SECRET" not in str(
                conn.execute("SELECT body FROM receipts").fetchall()
            )
            assert "SYNTHETIC_SECRET" not in str(
                conn.execute("SELECT data FROM profiles").fetchall()
            )


def test_scenario_order_duplicates_and_replay(store: EventStore) -> None:
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        app.state.planner.routes = FixedRoutes()
        sid = store.active_session()
        assert (
            post(client, "/demo/advance", dict(expected_session_id=sid, to_step="T+10")).status_code
            == 409
        )
        for step in ("T+0", "T+2", "T+5", "T+10"):
            key = str(uuid.uuid4())
            body = dict(expected_session_id=sid, to_step=step)
            response = post(client, "/demo/advance", body, key)
            assert response.status_code == 200, response.text
            head = store.state().as_of_sequence
            repeated = post(client, "/demo/advance", body, key)
            assert repeated.json() == response.json()
            assert store.state().as_of_sequence <= head + 1  # at most explicit revalidation
            p = store.state().current_proposal
            if p:
                accepted = post(
                    client,
                    f"/plans/{p.plan_id}/approve",
                    dict(
                        expected_session_id=sid,
                        expected_plan_version=p.version,
                        expected_planning_sequence=p.based_on_planning_sequence,
                        acknowledged_flag_ids=[f.flag_id for f in p.flags if f.requires_ack],
                    ),
                )
                assert accepted.status_code == 200, accepted.text
                app.state.planner.deliver()
        state = store.state()
        assert state.sim_time_s == 600
        assert next(u for u in state.units if u.unit_id == "unit_A2").status == "broken_down"
        assert any(i.duplicate_candidate_of for i in state.incidents)
        assert state_hash(store.state_at(state.session_id, state.as_of_sequence)) == state_hash(
            state
        )
        assert any(
            e.event_type == "HospitalPreAlertSimulated"
            for e in store.events(state.session_id, 0, 500)
        )
        with sqlite3.connect(store.path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM report_text").fetchone()[0] == 8


def test_same_key_is_scoped_to_method_path(store: EventStore) -> None:
    from app.storage.event_store import Decision

    key = str(uuid.uuid4())
    for path in ("/one", "/two"):
        result = store.execute(
            method="POST",
            path=path,
            key=key,
            body={},
            expected_session_id=store.active_session() or "",
            decide=lambda _: Decision([], lambda _: (200, {})),
            actor={"kind": "system", "id": "test"},
        )
        assert result.status == 200 and not result.replayed
