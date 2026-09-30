"""Small, dependency-free planar geometry on WGS 84 ``[lon, lat]`` positions.

Distances use the haversine formula. Polygon tests treat lon/lat as planar, which is
accurate to well under a metre at city scale and is only used for closure checks.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import pairwise

Coord = tuple[float, float]
Ring = Sequence[Sequence[float]]
EARTH_RADIUS_M = 6_371_008.8


def haversine_m(a: Sequence[float], b: Sequence[float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def point_in_ring(point: Sequence[float], ring: Ring) -> bool:
    x, y = point[0], point[1]
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def point_in_polygon(point: Sequence[float], rings: Sequence[Ring]) -> bool:
    """GeoJSON polygon: first ring is the exterior, the rest are holes."""
    if not rings or not point_in_ring(point, rings[0]):
        return False
    return not any(point_in_ring(point, hole) for hole in rings[1:])


def _orient(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Sequence[float], b: Sequence[float], p: Sequence[float]) -> bool:
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_intersect(
    p1: Sequence[float], p2: Sequence[float], q1: Sequence[float], q2: Sequence[float]
) -> bool:
    d1, d2 = _orient(q1, q2, p1), _orient(q1, q2, p2)
    d3, d4 = _orient(p1, p2, q1), _orient(p1, p2, q2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 and d2 and d3 and d4:
        return True
    return (
        (d1 == 0 and _on_segment(q1, q2, p1))
        or (d2 == 0 and _on_segment(q1, q2, p2))
        or (d3 == 0 and _on_segment(p1, p2, q1))
        or (d4 == 0 and _on_segment(p1, p2, q2))
    )


def polyline_touches_polygon(line: Sequence[Sequence[float]], rings: Sequence[Ring]) -> bool:
    """True if any vertex lies inside, or any segment crosses a ring boundary."""
    if any(point_in_polygon(p, rings) for p in line):
        return True
    for a, b in pairwise(line):
        for ring in rings:
            for i in range(len(ring) - 1):
                if segments_intersect(a, b, ring[i], ring[i + 1]):
                    return True
    return False


def bbox(points: Sequence[Sequence[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def bboxes_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]
