"""WebSocket sequence, catch-up, live delivery, heartbeat and reset protocol (0005)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

K1 = "11111111-1111-4111-8111-111111111111"
K2 = "22222222-2222-4222-8222-222222222222"


def _hello_and_subscribe(ws: Any, session: str, after: int) -> dict[str, Any]:
    hello: dict[str, Any] = ws.receive_json()
    assert hello["type"] == "hello" and hello["schema_version"] == "1.0"
    ws.send_json({"type": "subscribe", "session_id": session, "after_sequence": after})
    return hello


def test_backlog_then_caught_up_then_live(client: TestClient) -> None:
    session = client.get("/state").json()["session_id"]
    with client.websocket_connect("/ws/events") as ws:
        hello = _hello_and_subscribe(ws, session, 0)
        assert hello["head_sequence"] == 1
        first = ws.receive_json()
        assert first["type"] == "event" and first["event"]["event_type"] == "SessionStarted"
        assert ws.receive_json() == {"type": "caught_up", "head_sequence": 1}
        client.post(
            "/units/unit_A2/status",
            headers={"Idempotency-Key": K1},
            json={"to_status": "broken_down", "sim_time_s": 1, "expected_session_id": session},
        )
        live = ws.receive_json()
        while live["type"] == "heartbeat":
            live = ws.receive_json()
        assert live["event"]["sequence"] == 2 and live["event"]["event_type"] == "UnitStatusChanged"


def test_resume_after_sequence_skips_delivered_events(client: TestClient) -> None:
    session = client.get("/state").json()["session_id"]
    client.post(
        "/units/unit_A2/status",
        headers={"Idempotency-Key": K1},
        json={"to_status": "broken_down", "sim_time_s": 1, "expected_session_id": session},
    )
    with client.websocket_connect("/ws/events") as ws:
        _hello_and_subscribe(ws, session, 1)
        assert ws.receive_json()["event"]["sequence"] == 2
        assert ws.receive_json() == {"type": "caught_up", "head_sequence": 2}


def test_heartbeat_reports_last_delivered_sequence(client: TestClient) -> None:
    session = client.get("/state").json()["session_id"]
    with client.websocket_connect("/ws/events") as ws:
        _hello_and_subscribe(ws, session, 1)
        assert ws.receive_json()["type"] == "caught_up"
        assert ws.receive_json() == {"type": "heartbeat", "head_sequence": 1}


def test_wrong_session_or_future_sequence_requires_snapshot(client: TestClient) -> None:
    session = client.get("/state").json()["session_id"]
    with client.websocket_connect("/ws/events") as ws:
        _hello_and_subscribe(ws, "sess_9999", 0)
        assert ws.receive_json() == {"type": "snapshot_required", "session_id": session}
        ws.send_json({"type": "subscribe", "session_id": session, "after_sequence": 50})
        assert ws.receive_json()["type"] == "snapshot_required"
        ws.send_json({"type": "subscribe", "session_id": session, "after_sequence": 1})
        assert ws.receive_json() == {"type": "caught_up", "head_sequence": 1}


def test_reset_ends_subscription_with_snapshot_required(client: TestClient) -> None:
    session = client.get("/state").json()["session_id"]
    with client.websocket_connect("/ws/events") as ws:
        _hello_and_subscribe(ws, session, 1)
        assert ws.receive_json()["type"] == "caught_up"
        client.post(
            "/demo/reset",
            headers={"Idempotency-Key": K2},
            json={"fixture": "demo-bengaluru-v1", "seed": 7, "expected_session_id": session},
        )
        message = ws.receive_json()
        while message["type"] == "heartbeat":
            message = ws.receive_json()
        assert message == {"type": "snapshot_required", "session_id": "sess_0002"}
