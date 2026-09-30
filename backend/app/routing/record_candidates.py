"""Record route candidates for every active incident of a snapshot (mock/demo fixtures).

    uv run python -m app.routing.record_candidates SNAPSHOT.json OUT.json

The output is a list of contract ``RouteCandidates`` produced by the real router, so UI mocks
show genuine road routes instead of hand-drawn lines. Provenance is embedded in each item.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.contracts.state import StateSnapshot

from .service import RouteService


def record(state: StateSnapshot) -> list[dict[str, object]]:
    service = RouteService()
    return [
        service.candidates(state, incident.incident_id).model_dump(mode="json", by_alias=True)
        for incident in sorted(state.incidents, key=lambda i: i.incident_id)
        if incident.status == "active" and incident.category == "emergency"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    state = StateSnapshot.model_validate_json(args.snapshot.read_text())
    items = record(state)
    args.out.write_text(json.dumps(items, indent=1) + "\n")
    print(f"recorded {len(items)} incidents -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
