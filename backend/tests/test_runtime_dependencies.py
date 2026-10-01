"""The served app needs a WebSocket implementation that uvicorn can load.

Without one, uvicorn logs a warning and answers ``GET /ws/events`` with 404, so the console
never goes live. TestClient does not need it, which is why only this test catches it.
"""

import importlib.util


def test_uvicorn_websocket_implementation_is_installed() -> None:
    assert importlib.util.find_spec("websockets") is not None
