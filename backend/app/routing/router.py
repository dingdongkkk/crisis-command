"""Fastest road route on the recorded graph, avoiding closed flood polygons (0003 H5).

Rules that keep ETAs honest:
- No path, a closed destination/origin, or a location too far from any open road yields
  ``route_status: "unavailable"`` with a reason code and no duration — never a straight line.
- Only the short access legs between a location and its snapped road point (≤ SNAP_MAX_M)
  are straight; they are included in geometry, distance and time at ACCESS_SPEED_KPH.
- Deterministic: stable tie-breaking by node/edge index; results depend only on inputs.
"""

from __future__ import annotations

import hashlib
import heapq
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise

from app.contracts.entities import Route

from .geometry import (
    Coord,
    bbox,
    bboxes_overlap,
    haversine_m,
    point_in_polygon,
    polyline_touches_polygon,
)
from .graph import ACCESS_SPEED_KPH, Edge, RoadGraph, Snap

Polygon = Sequence[Sequence[Sequence[float]]]  # GeoJSON rings


@dataclass(frozen=True)
class Closure:
    flood_id: str
    version: int
    rings: tuple[tuple[tuple[float, float], ...], ...]


def closures_key(closures: Sequence[Closure]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((c.flood_id, c.version) for c in closures))


def flood_version(closures: Sequence[Closure]) -> int:
    return max((c.version for c in closures), default=0)


class Router:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph
        self._blocked_cache: dict[tuple[tuple[str, int], ...], frozenset[int]] = {}
        self._route = lru_cache(maxsize=4096)(self._route_uncached)

    # --- closures ---------------------------------------------------------------------

    def blocked_edges(self, closures: Sequence[Closure]) -> frozenset[int]:
        key = closures_key(closures)
        if key not in self._blocked_cache:
            blocked: set[int] = set()
            for closure in closures:
                exterior = closure.rings[0]
                box = bbox(exterior)
                for edge in self.graph.edges:
                    if bboxes_overlap(edge.bbox, box) and polyline_touches_polygon(
                        edge.coords, closure.rings
                    ):
                        blocked.add(edge.index)
            self._blocked_cache[key] = frozenset(blocked)
        return self._blocked_cache[key]

    # --- public API -------------------------------------------------------------------

    def route(self, origin: Coord, destination: Coord, closures: Sequence[Closure] = ()) -> Route:
        o = (round(origin[0], 6), round(origin[1], 6))
        d = (round(destination[0], 6), round(destination[1], 6))
        return self._route(o, d, tuple(sorted(closures, key=lambda c: (c.flood_id, c.version))))

    # --- implementation ---------------------------------------------------------------

    def _route_uncached(
        self, origin: Coord, destination: Coord, closures: tuple[Closure, ...]
    ) -> Route:
        fv = flood_version(closures)
        for closure in closures:
            if point_in_polygon(destination, closure.rings):
                return _unavailable(origin, destination, fv, "DESTINATION_IN_CLOSED_FLOOD_ZONE")
            if point_in_polygon(origin, closure.rings):
                return _unavailable(origin, destination, fv, "ORIGIN_IN_CLOSED_FLOOD_ZONE")
        blocked = self.blocked_edges(closures)
        starts = self.graph.snap_candidates(origin, blocked)
        goals = self.graph.snap_candidates(destination, blocked)
        if not starts:
            return _unavailable(origin, destination, fv, "ORIGIN_NOT_NEAR_OPEN_ROAD")
        if not goals:
            return _unavailable(origin, destination, fv, "DESTINATION_NOT_NEAR_OPEN_ROAD")
        found = self._search(starts, goals, destination, blocked)
        if found is None:
            return _unavailable(origin, destination, fv, "NO_OPEN_ROAD_PATH")
        duration, road_coords, start, goal = found
        coords = _dedupe([origin, start.point, *road_coords, goal.point, destination])
        if len(coords) < 2:
            coords = [origin, destination]
        distance = sum(haversine_m(a, b) for a, b in pairwise(coords))
        return Route.model_validate(
            {
                "route_id": _route_id(origin, destination, fv),
                "from": {"type": "Point", "coordinates": list(origin)},
                "to": {"type": "Point", "coordinates": list(destination)},
                "route_status": "ok",
                "provider": "fixture",
                "flood_version": fv,
                "duration_s": round(duration),
                "distance_m": round(distance),
                "geometry": {"type": "LineString", "coordinates": [list(c) for c in coords]},
            }
        )

    def _search(
        self, starts: list[Snap], goals: list[Snap], destination: Coord, blocked: frozenset[int]
    ) -> tuple[float, list[Coord], Snap, Snap] | None:
        """Multi-source, multi-target A* on travel time, including access legs.

        Returns (total seconds, road polyline, chosen start snap, chosen goal snap).
        """
        g = self.graph
        access = ACCESS_SPEED_KPH / 3.6

        def part(edge: Edge, metres: float) -> float:
            return metres / edge.length_m * edge.time_s if edge.length_m else 0.0

        best_total = float("inf")
        # ("direct", start i, goal j, _) or ("via", end node, goal j, entered goal edge at u)
        best_plan: tuple[str, int, int, bool] | None = None

        # Start and goal on the same edge, travelling in an allowed direction.
        for i, st in enumerate(starts):
            for j, gl in enumerate(goals):
                edge = g.edges[st.edge]
                if st.edge == gl.edge and (gl.offset_m >= st.offset_m or edge.two_way):
                    total = (st.distance_m + gl.distance_m) / access + part(
                        edge, abs(gl.offset_m - st.offset_m)
                    )
                    if total < best_total:
                        best_total, best_plan = total, ("direct", i, j, True)

        dist: dict[int, float] = {}
        # node -> (prev node, edge, forward, start index); prev node None for seeded nodes
        prev: dict[int, tuple[int | None, int, bool, int]] = {}
        heap: list[tuple[float, float, int]] = []

        def push(node: int, cost: float, entry: tuple[int | None, int, bool, int]) -> None:
            if cost < dist.get(node, float("inf")) - 1e-9:
                dist[node] = cost
                prev[node] = entry
                heapq.heappush(heap, (cost + self._h(node, destination), cost, node))

        for i, st in enumerate(starts):
            edge = g.edges[st.edge]
            leg = st.distance_m / access
            push(edge.v, leg + part(edge, edge.length_m - st.offset_m), (None, st.edge, True, i))
            if edge.two_way:
                push(edge.u, leg + part(edge, st.offset_m), (None, st.edge, False, i))

        # Finishing options: node -> (cost to reach destination, goal index, via u).
        finish: dict[int, tuple[float, int, bool]] = {}
        for j, gl in enumerate(goals):
            edge = g.edges[gl.edge]
            leg = gl.distance_m / access
            options = [(edge.u, leg + part(edge, gl.offset_m), True)]
            if edge.two_way:
                options.append((edge.v, leg + part(edge, edge.length_m - gl.offset_m), False))
            for node, cost, via_u in options:
                if cost < finish.get(node, (float("inf"), 0, True))[0]:
                    finish[node] = (cost, j, via_u)

        while heap:
            f, cost, node = heapq.heappop(heap)
            if f >= best_total:
                break
            if cost > dist.get(node, float("inf")):
                continue
            if node in finish and cost + finish[node][0] < best_total:
                best_total = cost + finish[node][0]
                best_plan = ("via", node, finish[node][1], finish[node][2])
            for edge_i, forward in g.outgoing[node]:
                if edge_i in blocked:
                    continue
                edge = g.edges[edge_i]
                push(edge.v if forward else edge.u, cost + edge.time_s, (node, edge_i, forward, -1))

        if best_plan is None:
            return None
        kind, a, j, via_u = best_plan
        goal = goals[j]
        t_edge = g.edges[goal.edge]
        if kind == "direct":
            start = starts[a]
            return (
                best_total,
                _slice(g.edges[start.edge], start.offset_m, goal.offset_m),
                start,
                goal,
            )

        chain: list[tuple[int, bool]] = []
        cursor: int | None = a
        first_forward, start_index = True, 0
        while cursor is not None:
            parent, edge_i, forward, index = prev[cursor]
            if parent is None:
                first_forward, start_index = forward, index
                break
            chain.append((edge_i, forward))
            cursor = parent
        chain.reverse()
        start = starts[start_index]
        s_edge = g.edges[start.edge]
        coords: list[Coord] = _slice(
            s_edge, start.offset_m, s_edge.length_m if first_forward else 0.0
        )
        for edge_i, forward in chain:
            e = g.edges[edge_i]
            coords += list(e.coords if forward else reversed(e.coords))
        coords += (
            _slice(t_edge, 0.0, goal.offset_m)
            if via_u
            else _slice(t_edge, t_edge.length_m, goal.offset_m)
        )
        return best_total, coords, start, goal

    def _h(self, node: int, goal: Coord) -> float:
        return haversine_m(self.graph.nodes[node], goal) / self.graph.max_speed_ms


def _slice(edge: Edge, a: float, b: float) -> list[Coord]:
    """Polyline points along ``edge`` from offset a to offset b (either direction)."""
    lo, hi = min(a, b), max(a, b)
    pts: list[Coord] = [_point_at(edge, lo)]
    for i, m in enumerate(edge.cumulative_m):
        if lo < m < hi:
            pts.append(edge.coords[i])
    pts.append(_point_at(edge, hi))
    return pts if a <= b else list(reversed(pts))


def _point_at(edge: Edge, offset: float) -> Coord:
    cum = edge.cumulative_m
    for i in range(len(cum) - 1):
        if cum[i] <= offset <= cum[i + 1]:
            span = cum[i + 1] - cum[i]
            t = 0.0 if span == 0 else (offset - cum[i]) / span
            a, b = edge.coords[i], edge.coords[i + 1]
            return (round(a[0] + t * (b[0] - a[0]), 6), round(a[1] + t * (b[1] - a[1]), 6))
    return edge.coords[-1]


def _dedupe(coords: Sequence[Coord]) -> list[Coord]:
    out: list[Coord] = []
    for c in coords:
        rc = (round(c[0], 6), round(c[1], 6))
        if not out or out[-1] != rc:
            out.append(rc)
    return out


def _route_id(origin: Coord, destination: Coord, fv: int) -> str:
    digest = hashlib.sha1(f"{origin}|{destination}|{fv}".encode()).hexdigest()[:12]
    return f"route_{digest}_fv{fv}"


def _unavailable(origin: Coord, destination: Coord, fv: int, reason: str) -> Route:
    return Route.model_validate(
        {
            "route_id": _route_id(origin, destination, fv),
            "from": {"type": "Point", "coordinates": list(origin)},
            "to": {"type": "Point", "coordinates": list(destination)},
            "route_status": "unavailable",
            "unavailable_reason": reason,
            "provider": "fixture",
            "flood_version": fv,
            "duration_s": None,
            "distance_m": None,
            "geometry": None,
        }
    )
