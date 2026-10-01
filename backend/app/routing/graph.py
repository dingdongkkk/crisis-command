"""Road graph loaded from the recorded fixture, with an exact-snap spatial index."""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass, field
from functools import cache
from itertools import pairwise
from pathlib import Path
from typing import Any

from .geometry import Coord, haversine_m

FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "evals"
    / "fixtures"
    / "roads"
    / "bengaluru-drive-v1.json.gz"
)

# Demonstration speeds for an emergency vehicle in urban traffic (km/h), by OSM class.
# Versioned policy values, not measured travel times; see docs/handoffs/CC-07.md.
ROUTING_POLICY_VERSION = "routing-demo-2026.1"
SPEED_KPH: dict[str, float] = {
    "motorway": 55,
    "motorway_link": 35,
    "trunk": 45,
    "trunk_link": 30,
    "primary": 35,
    "primary_link": 25,
    "secondary": 30,
    "secondary_link": 22,
    "tertiary": 25,
    "tertiary_link": 20,
    "unclassified": 20,
}
DEFAULT_SPEED_KPH = 20.0
ACCESS_SPEED_KPH = 12.0  # straight access leg between a location and its snapped road point
SNAP_MAX_M = 400.0
SNAP_SLACK_M = 60.0  # also consider other roads this much farther than the nearest
SNAP_LIMIT = 6
CELL_DEG = 0.004  # ~440 m grid cells for the snap index


@dataclass(frozen=True)
class Edge:
    index: int
    u: int
    v: int
    length_m: float
    time_s: float
    highway: str
    two_way: bool
    coords: tuple[Coord, ...]
    cumulative_m: tuple[float, ...]
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class Snap:
    edge: int
    offset_m: float  # distance from the edge's u end along its polyline
    point: Coord
    distance_m: float


@dataclass
class RoadGraph:
    version: str
    nodes: list[Coord]
    edges: list[Edge]
    outgoing: list[list[tuple[int, bool]]] = field(default_factory=list)  # (edge, forward)
    cells: dict[tuple[int, int], list[tuple[int, int]]] = field(
        default_factory=dict
    )  # -> (edge, segment)
    max_speed_ms: float = 1.0

    @classmethod
    def from_fixture(cls, data: dict[str, Any]) -> RoadGraph:
        classes: list[str] = data["highway_classes"]
        nodes: list[Coord] = [(float(x), float(y)) for x, y in data["nodes"]]
        edges: list[Edge] = []
        for i, (u, v, length, class_idx, oneway, flat) in enumerate(data["edges"]):
            highway = classes[class_idx]
            interior = [(flat[k], flat[k + 1]) for k in range(0, len(flat), 2)]
            coords = (nodes[u], *interior, nodes[v])
            cum = [0.0]
            for a, b in pairwise(coords):
                cum.append(cum[-1] + haversine_m(a, b))
            speed = SPEED_KPH.get(highway, DEFAULT_SPEED_KPH) / 3.6
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            edges.append(
                Edge(
                    i,
                    u,
                    v,
                    cum[-1] or float(length),
                    (cum[-1] or float(length)) / speed,
                    highway,
                    oneway == 0,
                    coords,
                    tuple(cum),
                    (min(xs), min(ys), max(xs), max(ys)),
                )
            )
        graph = cls(str(data["graph_version"]), nodes, edges)
        graph.outgoing = [[] for _ in nodes]
        for e in edges:
            graph.outgoing[e.u].append((e.index, True))
            if e.two_way:
                graph.outgoing[e.v].append((e.index, False))
            for s, (a, b) in enumerate(pairwise(e.coords)):
                for cell in _cells_for_segment(a, b):
                    graph.cells.setdefault(cell, []).append((e.index, s))
        graph.max_speed_ms = max(SPEED_KPH.values()) / 3.6
        return graph

    def snap(
        self, point: Coord, blocked: frozenset[int] = frozenset(), max_m: float = SNAP_MAX_M
    ) -> Snap | None:
        """Nearest point on any open road segment within ``max_m``."""
        found = self.snap_candidates(point, blocked, max_m)
        return found[0] if found else None

    def snap_candidates(
        self,
        point: Coord,
        blocked: frozenset[int] = frozenset(),
        max_m: float = SNAP_MAX_M,
        slack_m: float = SNAP_SLACK_M,
        limit: int = SNAP_LIMIT,
    ) -> list[Snap]:
        """Nearest point on each open road within ``best + slack_m`` (and ``max_m``).

        Several candidates matter on divided roads, ramps and flyovers, where the single
        nearest segment may be a one-way carriageway in the wrong direction. Ordered by
        distance, then edge index, so results are deterministic.
        """
        cx, cy = _cell(point)
        per_edge: dict[int, tuple[float, int, float, Coord]] = {}
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for edge_i, seg in self.cells.get((cx + dx, cy + dy), ()):
                    if edge_i in blocked:
                        continue
                    edge = self.edges[edge_i]
                    t, proj = _project(point, edge.coords[seg], edge.coords[seg + 1])
                    dist = haversine_m(point, proj)
                    if dist <= max_m and (edge_i not in per_edge or dist < per_edge[edge_i][0]):
                        per_edge[edge_i] = (dist, seg, t, proj)
        if not per_edge:
            return []
        best = min(v[0] for v in per_edge.values())
        ranked = sorted(
            (v[0], edge_i, v[1], v[2], v[3])
            for edge_i, v in per_edge.items()
            if v[0] <= best + slack_m
        )
        snaps = []
        for dist, edge_i, seg, t, proj in ranked[:limit]:
            edge = self.edges[edge_i]
            offset = edge.cumulative_m[seg] + t * (
                edge.cumulative_m[seg + 1] - edge.cumulative_m[seg]
            )
            snaps.append(Snap(edge_i, offset, (round(proj[0], 6), round(proj[1], 6)), dist))
        return snaps


def _cell(p: Coord) -> tuple[int, int]:
    return math.floor(p[0] / CELL_DEG), math.floor(p[1] / CELL_DEG)


def _cells_for_segment(a: Coord, b: Coord) -> set[tuple[int, int]]:
    (x0, y0), (x1, y1) = _cell(a), _cell(b)
    return {
        (x, y)
        for x in range(min(x0, x1), max(x0, x1) + 1)
        for y in range(min(y0, y1), max(y0, y1) + 1)
    }


def _project(p: Coord, a: Coord, b: Coord) -> tuple[float, Coord]:
    """Projection of p onto segment ab in a locally scaled plane; returns (t, point)."""
    k = math.cos(math.radians(p[1]))
    ax, ay, bx, by, px, py = a[0] * k, a[1], b[0] * k, b[1], p[0] * k, p[1]
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    t = 0.0 if denom == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return t, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


@cache
def load_default_graph() -> RoadGraph:
    with gzip.open(FIXTURE, "rt") as fh:
        return RoadGraph.from_fixture(json.load(fh))
