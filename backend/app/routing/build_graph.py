"""Build the recorded road-graph fixture from an Overpass (OpenStreetMap) download.

    uv run python -m app.routing.build_graph RAW.json \
        ../evals/fixtures/roads/bengaluru-drive-v1.json.gz

Input: Overpass JSON from ``way["highway"~...](bbox); out body geom;``. Output: a compact,
deterministic graph whose nodes are road junctions and dead ends, and whose edges are the
polylines between them. Speeds are *not* baked in; they come from the versioned routing
policy at load time. Data © OpenStreetMap contributors, ODbL-1.0.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any

from .geometry import haversine_m

GRAPH_FORMAT = 1
ONEWAY_BY_DEFAULT = {"motorway", "motorway_link"}


def _oneway(tags: dict[str, str]) -> int:
    """1 = forward only, -1 = reverse only, 0 = both directions."""
    value = tags.get("oneway", "")
    if value in ("yes", "true", "1"):
        return 1
    if value == "-1":
        return -1
    if value == "no":
        return 0
    if tags.get("junction") in ("roundabout", "circular"):
        return 1
    return 1 if tags.get("highway") in ONEWAY_BY_DEFAULT else 0


def build(raw: dict[str, Any], *, source_note: str) -> dict[str, Any]:
    ways = sorted(
        (w for w in raw["elements"] if w.get("type") == "way" and len(w.get("nodes", [])) >= 2),
        key=lambda w: w["id"],
    )
    coords: dict[int, tuple[float, float]] = {}
    uses: dict[int, int] = defaultdict(int)
    for way in ways:
        for nid, point in zip(way["nodes"], way["geometry"], strict=True):
            coords[nid] = (round(point["lon"], 6), round(point["lat"], 6))
        for nid in way["nodes"]:
            uses[nid] += 1
        uses[way["nodes"][0]] += 1  # endpoints are always graph nodes
        uses[way["nodes"][-1]] += 1

    classes = sorted({w["tags"]["highway"] for w in ways})
    class_index = {c: i for i, c in enumerate(classes)}
    raw_edges: list[tuple[int, int, int, int, list[int]]] = []  # u, v, class, oneway, interior
    for way in ways:
        direction = _oneway(way["tags"])
        nodes = way["nodes"] if direction != -1 else list(reversed(way["nodes"]))
        direction = 1 if direction == -1 else direction
        start = 0
        for i in range(1, len(nodes)):
            if uses[nodes[i]] > 1 or i == len(nodes) - 1:
                if nodes[start] != nodes[i]:
                    raw_edges.append(
                        (
                            nodes[start],
                            nodes[i],
                            class_index[way["tags"]["highway"]],
                            direction,
                            nodes[start + 1 : i],
                        )
                    )
                start = i

    # Keep the largest weakly connected component so every node can reach the core network.
    adjacency: dict[int, set[int]] = defaultdict(set)
    for u, v, *_ in raw_edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    seen: set[int] = set()
    best: set[int] = set()
    for root in sorted(adjacency):
        if root in seen:
            continue
        component = {root}
        stack = [root]
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in component:
                    component.add(nxt)
                    stack.append(nxt)
        seen |= component
        if len(component) > len(best):
            best = component

    node_ids = sorted(best)
    index = {nid: i for i, nid in enumerate(node_ids)}
    edges = []
    for u, v, cls, direction, interior in raw_edges:
        if u not in best:
            continue
        path = [coords[u], *(coords[n] for n in interior), coords[v]]
        length = sum(haversine_m(a, b) for a, b in pairwise(path))
        flat = [c for point in path[1:-1] for c in point]
        edges.append([index[u], index[v], round(length, 1), cls, direction, flat])

    lons = [coords[n][0] for n in node_ids]
    lats = [coords[n][1] for n in node_ids]
    return {
        "format": GRAPH_FORMAT,
        "graph_version": "bengaluru-drive-v1",
        "source": source_note,
        "license": "ODbL-1.0 — © OpenStreetMap contributors",
        "bbox": [min(lons), min(lats), max(lons), max(lats)],
        "highway_classes": classes,
        "nodes": [list(coords[n]) for n in node_ids],
        "edges": edges,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument(
        "--source", default="Overpass API extract, 2026-09-30, bbox 12.80,77.45,13.15,77.80"
    )
    args = parser.parse_args(argv)
    graph = build(json.loads(args.raw.read_text()), source_note=args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(graph, separators=(",", ":"))
    # Empty header name and mtime=0 keep the file byte-reproducible regardless of output path.
    with (
        args.out.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh,
    ):
        fh.write(text.encode())
    print(f"nodes={len(graph['nodes'])} edges={len(graph['edges'])} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
