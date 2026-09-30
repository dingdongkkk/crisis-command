"""Flood-aware routing: geometry, graph building, fastest paths, closures, API (CC-07)."""

from __future__ import annotations

import gzip
import json
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.contracts import ADAPTERS
from app.routing.build_graph import build
from app.routing.geometry import point_in_polygon, polyline_touches_polygon, segments_intersect
from app.routing.graph import SNAP_MAX_M, RoadGraph, load_default_graph
from app.routing.router import Closure, Router

SQUARE = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]]

# --- geometry -----------------------------------------------------------------------------


def test_geometry_primitives() -> None:
    assert point_in_polygon((0.5, 0.5), SQUARE)
    assert not point_in_polygon((1.5, 0.5), SQUARE)
    with_hole = [SQUARE[0], [(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6), (0.4, 0.4)]]
    assert not point_in_polygon((0.5, 0.5), with_hole)
    assert segments_intersect((-1, 0.5), (2, 0.5), (1, 0), (1, 1))
    assert not segments_intersect((-1, 2), (2, 2), (1, 0), (1, 1))
    assert polyline_touches_polygon([(-1.0, 0.5), (2.0, 0.5)], SQUARE)  # crosses, no vertex inside
    assert not polyline_touches_polygon([(-1.0, 2.0), (2.0, 2.0)], SQUARE)


# --- synthetic graph ----------------------------------------------------------------------
#
#   n0 ---- slow residential-like (unclassified), direct ---- n1
#    \                                                       /
#     n2 ======== fast primary detour ========= n3 ========
#
# The direct road is shorter; the primary detour is faster. n1->n4 is one-way.

LON0, LAT0 = 77.60, 12.97


def _p(dx_m: float, dy_m: float) -> tuple[float, float]:
    return (round(LON0 + dx_m / 108_500, 6), round(LAT0 + dy_m / 111_320, 6))


def _box(flood_id: str, version: int, x0: float, y0: float, x1: float, y1: float) -> Closure:
    ring = (_p(x0, y0), _p(x1, y0), _p(x1, y1), _p(x0, y1), _p(x0, y0))
    return Closure(flood_id, version, (ring,))


NODE_OFFSETS_M = [(0, 0), (3000, 0), (300, -300), (2700, -300), (3000, 1000), (9000, 9000)]


def _graph() -> RoadGraph:
    nodes = [list(_p(x, y)) for x, y in NODE_OFFSETS_M]
    edges = [
        [0, 1, 3000.0, 0, 0, []],  # unclassified, two-way (20 km/h)
        [0, 2, 424.0, 1, 0, []],  # primary (35 km/h)
        [2, 3, 2400.0, 1, 0, []],
        [3, 1, 424.0, 1, 0, []],
        [1, 4, 1000.0, 1, 1, []],  # one-way n1 -> n4
        [5, 5, 0.0, 1, 0, []],  # isolated node 5 (self-loop, never reachable)
    ]
    return RoadGraph.from_fixture(
        {
            "graph_version": "test",
            "highway_classes": ["unclassified", "primary"],
            "nodes": nodes,
            "edges": edges,
        }
    )


def _coords(route: Any) -> list[list[float]]:
    return [list(c) for c in route.geometry.coordinates]


def test_fastest_not_shortest() -> None:
    router = Router(_graph())
    route = router.route(_p(0, 0), _p(3000, 0))
    assert route.route_status == "ok"
    via_detour = any(abs(c[1] - _p(0, -300)[1]) < 1e-6 for c in _coords(route))
    assert via_detour, "should take the faster primary detour"
    assert route.distance_m is not None and route.distance_m > 3000
    assert route.duration_s is not None and route.duration_s < 3000 / (20 / 3.6)


def test_one_way_is_respected() -> None:
    router = Router(_graph())
    forward = router.route(_p(3000, 0), _p(3000, 1000))
    backward = router.route(_p(3000, 1000), _p(3000, 0))
    assert forward.route_status == "ok"
    assert (
        backward.route_status == "unavailable"
        and backward.unavailable_reason == "NO_OPEN_ROAD_PATH"
    )


def test_closure_forces_detour_or_blocks() -> None:
    router = Router(_graph())
    # Close the primary detour: the route must fall back to the slower direct road.
    detour_box = _box("f", 1, 1000, -400, 2000, -200)
    open_route = router.route(_p(0, 0), _p(3000, 0))
    closed_route = router.route(_p(0, 0), _p(3000, 0), [detour_box])
    assert closed_route.route_status == "ok" and closed_route.flood_version == 1
    assert (closed_route.duration_s or 0) > (open_route.duration_s or 0)
    assert not any(abs(c[1] - _p(0, -300)[1]) < 1e-6 for c in _coords(closed_route))
    # A destination inside a closure is unavailable, never an estimate.
    around_dest = _box("g", 2, 2900, -100, 3100, 100)
    blocked = router.route(_p(0, 0), _p(3000, 0), [around_dest])
    assert blocked.route_status == "unavailable"
    assert blocked.unavailable_reason == "DESTINATION_IN_CLOSED_FLOOD_ZONE"
    assert blocked.duration_s is None and blocked.geometry is None


def test_snap_limit_and_isolated_nodes() -> None:
    router = Router(_graph())
    far = router.route(_p(0, 0), _p(3000, 3000))
    assert far.unavailable_reason == "DESTINATION_NOT_NEAR_OPEN_ROAD"
    near = router.route(_p(0, 0), _p(1500, SNAP_MAX_M - 50))
    assert near.route_status == "ok"


def test_same_edge_and_determinism() -> None:
    router = Router(_graph())
    a = router.route(_p(500, 0), _p(1500, 0))
    b = Router(_graph()).route(_p(500, 0), _p(1500, 0))
    assert a == b
    assert a.distance_m is not None and 950 <= a.distance_m <= 1050


def test_routes_are_contract_valid() -> None:
    router = Router(_graph())
    for route in (
        router.route(_p(0, 0), _p(3000, 0)),
        router.route(_p(3000, 1000), _p(3000, 0)),
    ):
        dumped = route.model_dump(mode="json", by_alias=True)
        assert ADAPTERS["Route"].validate_python(dumped)


# --- graph builder ------------------------------------------------------------------------


def _way(
    wid: int, nodes: list[int], tags: dict[str, str], coords: dict[int, tuple[float, float]]
) -> dict[str, Any]:
    return {"type": "way", "id": wid, "nodes": nodes, "tags": tags,
            "geometry": [{"lon": coords[n][0], "lat": coords[n][1]} for n in nodes]}  # fmt: skip


def test_builder_splits_at_junctions_and_orients_one_ways(tmp_path: Path) -> None:
    c = {
        1: (77.60, 12.97),
        2: (77.61, 12.97),
        3: (77.62, 12.97),
        4: (77.61, 12.98),
        9: (77.70, 13.0),
        10: (77.71, 13.0),
    }
    raw = {"elements": [
        _way(100, [1, 2, 3], {"highway": "primary"}, c),
        _way(101, [4, 2], {"highway": "tertiary", "oneway": "-1"}, c),  # stored reversed: 2 -> 4
        _way(102, [9, 10], {"highway": "primary"}, c),  # separate component, dropped
    ]}  # fmt: skip
    graph = build(raw, source_note="test")
    assert len(graph["nodes"]) == 4
    pairs = {
        (tuple(graph["nodes"][u]), tuple(graph["nodes"][v]), one)
        for u, v, _, _, one, _ in graph["edges"]
    }
    assert ((77.61, 12.97), (77.61, 12.98), 1) in pairs  # oneway=-1 reversed to forward
    assert len(graph["edges"]) == 3  # 1-2, 2-3 split at junction 2, plus 2->4
    assert build(raw, source_note="test") == graph


def test_committed_fixture_matches_format() -> None:
    fixture = (
        Path(__file__).resolve().parents[2]
        / "evals"
        / "fixtures"
        / "roads"
        / "bengaluru-drive-v1.json.gz"
    )
    with gzip.open(fixture, "rt") as fh:
        data = json.load(fh)
    assert data["format"] == 1 and "OpenStreetMap" in data["license"]
    assert len(data["nodes"]) > 10_000 and len(data["edges"]) > 10_000


# --- real Bengaluru graph -----------------------------------------------------------------

BELLANDUR = Closure(
    "flood_bellandur", 1,
    (((77.668, 12.924), (77.69, 12.924), (77.69, 12.938), (77.668, 12.938), (77.668, 12.924)),),
)  # fmt: skip
STATIONS = {
    "unit_A1": (77.607, 12.975), "unit_B1": (77.5946, 12.9716), "unit_B2": (77.5838, 12.925),
    "unit_B3": (77.592, 13.0358), "unit_F1": (77.601, 12.978), "unit_F2": (77.7, 12.96),
    "unit_T1": (77.66, 12.95),
}  # fmt: skip
SCHOOL = (77.5838, 12.93)
SILK_BOARD = (77.6229, 12.9177)
STRANDED_CAR = (77.6784, 12.9304)


@pytest.fixture(scope="module")
def real_router() -> Router:
    return Router(load_default_graph())


def test_every_station_reaches_the_school_by_road(real_router: Router) -> None:
    for unit, station in STATIONS.items():
        route = real_router.route(station, SCHOOL)
        assert route.route_status == "ok", unit
        coords = _coords(route)
        assert coords[0] == list(station) and coords[-1] == list(SCHOOL)
        assert len(coords) > 10, "follows the road network, not a straight line"
    nearest = min(STATIONS, key=lambda u: real_router.route(STATIONS[u], SCHOOL).duration_s or 1e9)
    assert nearest == "unit_B2"  # stationed 500 m away


def test_flood_blocks_destination_and_forces_detours(real_router: Router) -> None:
    assert real_router.route(STATIONS["unit_T1"], STRANDED_CAR, [BELLANDUR]).unavailable_reason == (
        "DESTINATION_IN_CLOSED_FLOOD_ZONE"
    )
    dry = real_router.route(STATIONS["unit_F2"], SILK_BOARD)
    wet = real_router.route(STATIONS["unit_F2"], SILK_BOARD, [BELLANDUR])
    assert dry.route_status == wet.route_status == "ok"
    assert (wet.duration_s or 0) > (dry.duration_s or 0)
    blocked = real_router.blocked_edges([BELLANDUR])
    graph = real_router.graph
    assert blocked and all(
        polyline_touches_polygon(graph.edges[i].coords, BELLANDUR.rings) for i in blocked
    )


def test_routing_is_fast_enough_for_replanning(real_router: Router) -> None:
    started = time.perf_counter()
    for station in STATIONS.values():
        for target in (SCHOOL, SILK_BOARD, (77.6408, 12.9784), (77.6387, 12.9116)):
            real_router.route(station, target, [BELLANDUR])
    assert time.perf_counter() - started < 3.0  # 28 routes on a laptop; measured ~0.1 s


# --- API ----------------------------------------------------------------------------------


def test_route_endpoint_and_candidates(client: TestClient) -> None:
    response = client.get(
        "/routing/route",
        params={"from_lon": 77.5838, "from_lat": 12.925, "to_lon": 77.6229, "to_lat": 12.9177},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert (
        body["route_status"] == "ok"
        and body["provider"] == "fixture"
        and body["flood_version"] == 0
    )
    session = client.get("/state").json()["session_id"]
    # No incidents in a fresh session: candidates for an unknown incident is a 404 problem.
    missing = client.get("/routing/candidates", params={"incident_id": "inc_9999"})
    assert missing.status_code == 404 and missing.json()["code"] == "NOT_FOUND"
    assert session


def test_candidates_use_current_flood_state(client: TestClient) -> None:
    from app.contracts.state import StateSnapshot
    from app.routing.service import UNAVAILABLE_STATUSES, RouteService, active_closures
    from tests.fixtures import load

    state = StateSnapshot.model_validate(load("world.before.json"))
    service = RouteService()
    result = service.candidates(state, "inc_0003")  # flood-stranded vehicle inside Bellandur flood
    assert ADAPTERS["RouteCandidates"].validate_python(
        result.model_dump(mode="json", by_alias=True)
    )
    assert active_closures(state) and result.flood_version == 1
    road = [c for c in result.candidates if c.unit_type != "boat"]
    assert all(c.route.unavailable_reason == "DESTINATION_IN_CLOSED_FLOOD_ZONE" for c in road)
    # A2 breaks down at seq 58 in the scenario; apply that here to test ordering.
    units = [
        u.model_copy(update={"status": "broken_down"}) if u.unit_id == "unit_A2" else u
        for u in state.units
    ]
    accident = service.candidates(state.model_copy(update={"units": units}), "inc_0004")
    ready = [
        c
        for c in accident.candidates
        if c.route.route_status == "ok" and c.unit_status not in UNAVAILABLE_STATUSES
    ]
    durations = [c.route.duration_s or 0 for c in ready]
    assert ready and durations == sorted(durations)
    # Units that cannot take tasks sort after every ready unit.
    order = [c.unit_id for c in accident.candidates]
    assert order.index("unit_A2") > max(order.index(c.unit_id) for c in ready)


def test_new_flood_version_invalidates_cached_routes() -> None:
    router = Router(_graph())
    far_away = _box("flood_x", 1, 8000, 8000, 8500, 8500)  # v1 touches nothing on the route
    over_detour = _box("flood_x", 2, 1000, -400, 2000, -200)  # v2 grows over the fast detour
    v1 = router.route(_p(0, 0), _p(3000, 0), [far_away])
    v2 = router.route(_p(0, 0), _p(3000, 0), [over_detour])
    assert (v1.flood_version, v2.flood_version) == (1, 2)
    assert v1.route_id != v2.route_id
    assert (v2.duration_s or 0) > (v1.duration_s or 0)  # recomputed, not served from the v1 cache
    assert router.route(_p(0, 0), _p(3000, 0), [far_away]) == v1  # v1 still cached and stable


def test_divided_road_snapping_picks_the_right_carriageway(real_router: Router) -> None:
    """Regression: the single nearest segment was a one-way ramp in the wrong direction,
    turning a 35 m gap at Silk Board into a 10 km loop. Multi-candidate snapping fixes it."""
    route = real_router.route((77.623, 12.918), SILK_BOARD)
    assert route.route_status == "ok"
    assert (route.distance_m or 0) < 500 and (route.duration_s or 0) < 120
