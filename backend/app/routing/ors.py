"""Optional bounded ORS Directions adapter. No route is replaced with an invented ETA.

API: https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import httpx
from pydantic import ValidationError

from app.contracts.entities import Route
from app.contracts.state import StateSnapshot
from app.routing.geometry import Coord, polyline_touches_polygon
from app.routing.router import flood_version
from app.routing.service import active_closures


class OrsDirections:
    def __init__(self, key: str, *, client: httpx.Client | None = None) -> None:
        self.key = key
        self.client = client or httpx.Client(timeout=httpx.Timeout(2.0), follow_redirects=False)
        self.cache: dict[str, Route] = {}

    def route(self, state: StateSnapshot, origin: Coord, destination: Coord) -> Route:
        closures = active_closures(state)
        body: dict[str, Any] = {
            "coordinates": [origin, destination],
            "units": "m",
            "instructions": False,
        }
        if closures:
            body["options"] = {
                "avoid_polygons": {
                    "type": "MultiPolygon",
                    "coordinates": [c.rings for c in closures],
                }
            }
        digest = hashlib.sha256(
            json.dumps([body, [(c.flood_id, c.version) for c in closures]], sort_keys=True).encode()
        ).hexdigest()[:20]
        if digest in self.cache:
            return self.cache[digest].model_copy(deep=True)
        base: dict[str, Any] = {
            "route_id": f"ors_{digest}",
            "from": {"type": "Point", "coordinates": origin},
            "to": {"type": "Point", "coordinates": destination},
            "provider": "ors_directions",
            "flood_version": flood_version(closures),
        }
        cause = "ORS_NOT_CONFIGURED"
        if self.key:
            try:
                response = self.client.post(
                    "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
                    headers={"Authorization": self.key},
                    json=body,
                    timeout=2.0,
                )
                response.raise_for_status()
                feature = response.json()["features"][0]
                geometry = feature["geometry"]
                summary = feature["properties"]["summary"]
                coords = geometry["coordinates"]
                if any(polyline_touches_polygon(coords, c.rings) for c in closures):
                    raise ValueError("route crosses closure")
                route = Route.model_validate(
                    {
                        **base,
                        "route_status": "ok",
                        "duration_s": math.ceil(summary["duration"]),
                        "distance_m": math.ceil(summary["distance"]),
                        "geometry": geometry,
                    }
                )
                if len(self.cache) >= 2048:
                    self.cache.clear()
                self.cache[digest] = route
                return route.model_copy(deep=True)
            except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError, ValidationError):
                cause = "ORS_UNAVAILABLE_OR_INVALID"
        return Route.model_validate(
            {
                **base,
                "route_status": "provider_error",
                "duration_s": None,
                "distance_m": None,
                "geometry": None,
                "unavailable_reason": cause,
            }
        )
