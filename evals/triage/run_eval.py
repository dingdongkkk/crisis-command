#!/usr/bin/env python3
"""Run the triage evaluation (rule adapter; no network, no API key).

cd backend && uv run python ../evals/triage/run_eval.py [--json ../evals/triage/report.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "backend"))

from app.intake.evaluation import evaluate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write the combined report here")
    args = parser.parse_args()
    names = ("cases.dev.jsonl", "cases.heldout.jsonl", "cases.cc11.jsonl")
    reports = [evaluate(HERE / name).as_dict() for name in names]
    for r in reports:
        print(
            f"{r['dataset']}: {r['passed']}/{r['cases']} cases fully correct · "
            f"unsafe downgrades {r['unsafe_downgrades']} · missed danger {r['missed_danger']} · "
            f"over-triage {r['false_danger']} · category {r['category_accuracy']} · "
            f"escalations {r['required_escalations_met']}"
        )
        for f in r["failures"]:
            print(f"  {f['id']} [{f['lang']}]: " + "; ".join(f["errors"]))
    if args.json:
        args.json.write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n")
    return 1 if any(r["unsafe_downgrades"] for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
