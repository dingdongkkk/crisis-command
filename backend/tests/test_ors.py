from __future__ import annotations

import httpx

from app.routing.ors import OrsDirections
from app.storage.event_store import EventStore


def test_ors_timeout_no_eta(store: EventStore) -> None:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("offline", request=request)

    routes = OrsDirections(
        "synthetic", client=httpx.Client(transport=httpx.MockTransport(unavailable))
    )
    route = routes.route(store.state(), (77.6, 12.97), (77.61, 12.98))
    assert route.route_status == "provider_error"
    assert route.duration_s is None and route.geometry is None


def test_ors_units_and_cache(store: EventStore) -> None:
    calls = []

    def answer(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {"summary": {"duration": 12.1, "distance": 100.3}},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[77.6, 12.97], [77.61, 12.98]],
                        },
                    }
                ]
            },
        )

    routes = OrsDirections("synthetic", client=httpx.Client(transport=httpx.MockTransport(answer)))
    first = routes.route(store.state(), (77.6, 12.97), (77.61, 12.98))
    second = routes.route(store.state(), (77.6, 12.97), (77.61, 12.98))
    assert first.duration_s == 13 and first.distance_m == 101
    assert first == second and len(calls) == 1
