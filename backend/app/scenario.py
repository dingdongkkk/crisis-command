"""Run the backend synthetic scenario against an isolated database; never send real dispatch."""

from __future__ import annotations

import argparse
import json
import tempfile
import uuid
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi.testclient import TestClient

from app.domain.projection import state_hash
from app.main import create_app
from app.storage.event_store import EventStore


def run(path: Path) -> dict[str, Any]:
    store = EventStore(path)
    stages = []
    app = create_app(store=store, auto_plan=False)
    with TestClient(app) as client:
        session = store.active_session()
        for step in ("T+0", "T+2", "T+5", "T+10"):
            started = perf_counter()
            response = client.post(
                "/demo/advance",
                json={"expected_session_id": session, "to_step": step},
                headers={"Idempotency-Key": str(uuid.uuid4())},
            )
            response.raise_for_status()
            state = store.state()
            plan = state.current_proposal
            if plan:
                response = client.post(
                    f"/plans/{plan.plan_id}/approve",
                    json={
                        "expected_session_id": session,
                        "expected_plan_version": plan.version,
                        "expected_planning_sequence": plan.based_on_planning_sequence,
                        "acknowledged_flag_ids": [f.flag_id for f in plan.flags if f.requires_ack],
                        "note": "Synthetic acceptance runner",
                    },
                    headers={"Idempotency-Key": str(uuid.uuid4())},
                )
                response.raise_for_status()
                app.state.planner.deliver()
            stages.append(
                {
                    "step": step,
                    "elapsed_ms": round((perf_counter() - started) * 1000),
                    "plan": {
                        "plan_id": plan.plan_id,
                        "solver": plan.solver.model_dump(mode="json"),
                        "assignments": [
                            a.model_dump(mode="json", exclude={"route", "onward_route"})
                            for a in plan.assignments
                        ],
                        "unmet_needs": [n.model_dump(mode="json") for n in plan.unmet_needs],
                        "flags": [f.model_dump(mode="json") for f in plan.flags],
                    }
                    if plan
                    else None,
                }
            )
        state = store.state()
        assert state_hash(state) == state_hash(
            store.state_at(state.session_id, state.as_of_sequence)
        )
    return {"simulated": True, "replay_equal": True, "stages": stages}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="crisis-demo-") as directory:
        report = run(Path(directory) / "scenario.db")
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
