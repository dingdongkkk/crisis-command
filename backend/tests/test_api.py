"""HTTP contract behaviour for CC-03 commands, reads and problem details."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.contracts.common import Problem
from tests.fixtures import load

K1 = "11111111-1111-4111-8111-111111111111"
K2 = "22222222-2222-4222-8222-222222222222"
FLOOD = next(c for c in load("api.examples.json") if c["name"] == "flood_event_valid")


def _session(client: TestClient) -> str:
    return str(client.get("/state").json()["session_id"])


def _status(client: TestClient, key: str | None, **body: Any) -> Any:
    headers = {"Idempotency-Key": key} if key else {}
    return client.post("/units/unit_A2/status", json=body, headers=headers)


def _problem(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    body: dict[str, Any] = response.json()
    Problem.model_validate(body)
    assert body["code"] == code
    return body


def test_missing_and_malformed_idempotency_key(client: TestClient) -> None:
    body = {"to_status": "broken_down", "sim_time_s": 1, "expected_session_id": _session(client)}
    _problem(_status(client, None, **body), 400, "IDEMPOTENCY_KEY_MISSING")
    _problem(_status(client, "not-a-uuid", **body), 422, "VALIDATION_FAILED")


def test_unit_status_replay_and_reuse(client: TestClient) -> None:
    body = {"to_status": "broken_down", "sim_time_s": 1, "expected_session_id": _session(client)}
    first = _status(client, K1, **body)
    assert first.status_code == 200 and "idempotent-replayed" not in first.headers
    again = _status(client, K1, **body)
    assert again.headers["idempotent-replayed"] == "true" and again.json() == first.json()
    _problem(
        _status(client, K1, **{**body, "to_status": "off_duty"}), 422, "IDEMPOTENCY_KEY_REUSED"
    )


def test_invalid_transition_and_unknown_unit(client: TestClient) -> None:
    session = _session(client)
    _problem(
        _status(client, K1, to_status="on_scene", sim_time_s=1, expected_session_id=session),
        409,
        "INVALID_TRANSITION",
    )
    response = client.post(
        "/units/unit_ZZ/status",
        headers={"Idempotency-Key": K2},
        json={"to_status": "off_duty", "sim_time_s": 1, "expected_session_id": session},
    )
    _problem(response, 404, "NOT_FOUND")


def test_flood_versions_and_geometry_validation(client: TestClient) -> None:
    body = {**FLOOD["request"]["body"], "expected_session_id": _session(client)}
    created = client.post("/flood-events", json=body, headers={"Idempotency-Key": K1})
    assert created.status_code == 201 and created.json()["version"] == 1
    assert client.get("/state").json()["flood"][0]["flood_id"] == "flood_bellandur"
    _problem(
        client.post("/flood-events", json=body, headers={"Idempotency-Key": K2}),
        409,
        "INVALID_TRANSITION",
    )
    broken = {
        **body,
        "version": 2,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[77.6, 12.9], [77.7, 12.9], [77.7, 13.0]]],
        },
    }
    invalid = _problem(
        client.post("/flood-events", json=broken, headers={"Idempotency-Key": K2}),
        422,
        "VALIDATION_FAILED",
    )
    assert invalid["errors"][0]["pointer"].startswith("/geometry/coordinates")
    assert "POLYGON_RING_INVALID" in invalid["errors"][0]["message"]


def test_events_feed_and_snapshot_required(client: TestClient) -> None:
    session = _session(client)
    _status(client, K1, to_status="broken_down", sim_time_s=1, expected_session_id=session)
    events = client.get("/events", params={"session_id": session}).json()
    assert [e["sequence"] for e in events] == [1, 2]
    assert (
        client.get("/events", params={"session_id": session, "after_sequence": 1}).json()[0][
            "sequence"
        ]
        == 2
    )
    _problem(client.get("/events", params={"session_id": "sess_old"}), 410, "SNAPSHOT_REQUIRED")
    _problem(
        client.get("/events", params={"session_id": session, "after_sequence": 9}),
        410,
        "SNAPSHOT_REQUIRED",
    )


def test_replay_state_at_sequence(client: TestClient) -> None:
    session = _session(client)
    _status(client, K1, to_status="broken_down", sim_time_s=1, expected_session_id=session)
    replayed = client.get("/state", params={"at_sequence": 1, "session_id": session}).json()
    assert replayed["as_of_sequence"] == 1
    assert next(u for u in replayed["units"] if u["unit_id"] == "unit_A2")["status"] == "available"
    _problem(client.get("/state", params={"at_sequence": 1}), 422, "VALIDATION_FAILED")
    _problem(
        client.get("/state", params={"at_sequence": 99, "session_id": session}), 404, "NOT_FOUND"
    )
    assert len(client.get("/events", params={"session_id": session}).json()) == 2


def test_reset_boundary_and_stale_session(client: TestClient) -> None:
    old = _session(client)
    reset = {"fixture": "demo-bengaluru-v1", "seed": 7, "expected_session_id": old}
    first = client.post("/demo/reset", json=reset, headers={"Idempotency-Key": K1})
    assert first.status_code == 200 and first.json() == {
        "session_id": "sess_0002",
        "head_sequence": 1,
    }
    retry = client.post("/demo/reset", json=reset, headers={"Idempotency-Key": K1})
    assert retry.json() == first.json() and retry.headers["idempotent-replayed"] == "true"
    assert _session(client) == "sess_0002"
    stale = _status(client, K2, to_status="broken_down", sim_time_s=1, expected_session_id=old)
    assert _problem(stale, 409, "STALE_SESSION")["current"] == {"session_id": "sess_0002"}
    assert client.get("/state").json()["as_of_sequence"] == 1


def test_openapi_documents_problem_responses(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert "/units/{unit_id}/status" in spec["paths"] and "/events" in spec["paths"]
