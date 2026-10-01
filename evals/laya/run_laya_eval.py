#!/usr/bin/env python3
"""CC-14: evaluate Laya (typed-decision classifier) as an optional triage adapter.

Runs in its own environment; the backend never depends on it:

    uv venv .laya-venv && VIRTUAL_ENV=.laya-venv uv pip install "laya==0.3.22" "pydantic>=2.9"
    HF_HOME=/path/to/cache .laya-venv/bin/python evals/laya/run_laya_eval.py \\
        --checkpoint multilingual --device cpu --json evals/laya/results.json

For every labelled case in evals/triage, one batched Laya call asks each critical fact as a
tri-state choice (yes / no / unknown) and the category as a choice. Scoring matches
``app.intake.evaluation``: unsafe downgrades (safe value without evidence) must be zero.
It also scores the only adoption mode the app permits (0002): rules first, the model may only
*raise* a fact from unknown to its dangerous value, never lower anything.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.intake.facts import COUNT_FACTS, CRITICAL_FACTS, DANGEROUS_VALUE, safe_value  # noqa: E402
from app.intake.session import IntakeSession  # noqa: E402

SETS = ("cases.dev.jsonl", "cases.heldout.jsonl", "cases.cc11.jsonl")
BINARY = [k for k in CRITICAL_FACTS if k not in COUNT_FACTS]
WORDING = {
    "conscious": "Is the patient conscious and responsive?",
    "breathing_normally": "Is the patient breathing normally?",
    "chest_pain": "Does someone have chest pain?",
    "severe_bleeding": "Is someone bleeding heavily?",
    "trapped": "Is anyone trapped or unable to get out?",
    "fire_or_smoke": "Is there fire or smoke?",
    "gas_smell": "Is there a smell of gas or a gas leak?",
    "water_rising": "Is flood water rising around the people?",
    "caller_in_danger": "Is the caller in danger right now?",
}


def questions() -> dict[str, Any]:
    q: dict[str, Any] = {
        key: {
            "type": "choice",
            "instructions": f"{WORDING[key]} Answer only from what the caller says.",
            "criteria": {
                "yes": "the message clearly says so",
                "no": "the message clearly says the opposite",
                "unknown": "the message does not say, or is unclear",
            },
        }
        for key in BINARY
    }
    q["category"] = {
        "type": "choice",
        "instructions": "What kind of call is this?",
        "criteria": {
            "emergency": "someone may be hurt or in danger, or there is a hazard",
            "non_emergency_assist": "roadside help such as a flat tyre or breakdown, nobody hurt",
            "information_request": "a question about roads, traffic or services",
        },
    }
    return q


def load(name: str) -> list[dict[str, Any]]:
    path = ROOT / "evals" / "triage" / name
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def rules_facts(text: str) -> tuple[dict[str, str], str]:
    session = IntakeSession("inc_eval")
    session.add_report("rpt_eval", text, 0)
    facts = {f.key: f for f in session.triage_facts(0).facts}
    out = {}
    for key in BINARY:
        f = facts[key]
        out[key] = "unknown" if f.conflict else (f.value.value if f.value else "unknown")
    return out, session.category


def score(pred: dict[str, str], gold: dict[str, str]) -> dict[str, int]:
    s = {"unsafe_downgrades": 0, "missed_danger": 0, "false_danger": 0, "fact_errors": 0}
    for key in BINARY:
        want, got = gold.get(key, "unknown"), pred[key]
        s["fact_errors"] += got != want
        if got == safe_value(key) and want != safe_value(key):
            s["unsafe_downgrades"] += 1
        if want == DANGEROUS_VALUE[key] and got != DANGEROUS_VALUE[key]:
            s["missed_danger"] += 1
        if got == DANGEROUS_VALUE[key] and want != DANGEROUS_VALUE[key]:
            s["false_danger"] += 1
    return s


def calibration(pairs: list[tuple[float, int]], bins: int = 10) -> dict[str, float]:
    """Brier score and expected calibration error for P(dangerous value)."""
    if not pairs:
        return {"brier": float("nan"), "ece": float("nan")}
    brier = statistics.fmean((p - y) ** 2 for p, y in pairs)
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        group = [(p, y) for p, y in pairs if lo <= p < hi or (b == bins - 1 and p == 1.0)]
        if group:
            ece += (
                len(group)
                / len(pairs)
                * abs(statistics.fmean(p for p, _ in group) - statistics.fmean(y for _, y in group))
            )
    return {"brier": round(brier, 4), "ece": round(ece, 4)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--checkpoint", default="multilingual", choices=["english", "multilingual"])
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--raise-threshold", type=float, default=0.8)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    import importlib.metadata as md

    import laya

    t0 = perf_counter()
    kwargs: dict[str, Any] = {"device": args.device}
    if args.checkpoint == "multilingual":
        kwargs["subfolder"] = "multilingual"
    agent = laya.load("convaiinnovations/laya", **kwargs)
    load_s = perf_counter() - t0
    qs = questions()
    agent.predict({"body": "warm-up"}, qs)

    report: dict[str, Any] = {
        "adapter": "laya",
        "checkpoint": f"convaiinnovations/laya ({args.checkpoint})",
        "laya_version": md.version("laya"),
        "torch_version": md.version("torch"),
        "device": args.device,
        "machine": f"{platform.platform()} {platform.machine()}",
        "load_seconds": round(load_s, 1),
        "raise_threshold": args.raise_threshold,
        "sets": {},
        "cases": [],
    }
    all_latency: list[float] = []
    all_cal: list[tuple[float, int]] = []
    for name in SETS:
        totals: dict[str, dict[str, int]] = {
            m: {
                "unsafe_downgrades": 0,
                "missed_danger": 0,
                "false_danger": 0,
                "fact_errors": 0,
                "category_correct": 0,
                "fully_correct": 0,
            }
            for m in ("rules", "laya", "hybrid")
        }
        cases = load(name)
        for case in cases:
            gold = {k: str(v) for k, v in case["expect"]["facts"].items() if k in BINARY}
            started = perf_counter()
            result = agent.predict({"body": case["text"]}, qs)
            latency = (perf_counter() - started) * 1000
            all_latency.append(latency)
            answers = result["answers"]
            model = {k: answers[k]["choice"] for k in BINARY}
            probs = {k: answers[k]["probabilities"] for k in BINARY}
            rules, rules_cat = rules_facts(case["text"])
            # 0002 adoption: rules first; model may only raise unknown -> dangerous, confidently.
            hybrid = dict(rules)
            for k in BINARY:
                danger = DANGEROUS_VALUE[k]
                if (
                    rules[k] == "unknown"
                    and model[k] == danger
                    and probs[k].get(danger, 0) >= args.raise_threshold
                ):
                    hybrid[k] = danger
            for k in BINARY:
                p = probs[k].get(DANGEROUS_VALUE[k], 0.0)
                all_cal.append((float(p), int(gold.get(k, "unknown") == DANGEROUS_VALUE[k])))
            cats = {"rules": rules_cat, "laya": answers["category"]["choice"], "hybrid": rules_cat}
            row: dict[str, Any] = {
                "set": name,
                "id": case["id"],
                "lang": case["lang"],
                "latency_ms": round(latency, 1),
            }
            for mode, pred in (("rules", rules), ("laya", model), ("hybrid", hybrid)):
                s = score(pred, gold)
                ok_cat = cats[mode] == case["expect"]["category"]
                for key, value in s.items():
                    totals[mode][key] += value
                totals[mode]["category_correct"] += ok_cat
                totals[mode]["fully_correct"] += s["fact_errors"] == 0 and ok_cat
                row[mode] = {"facts": pred, "category": cats[mode], **s}
            report["cases"].append(row)
        report["sets"][name] = {"cases": len(cases), **totals}

        def trio(metric: str, totals: dict[str, dict[str, int]] = totals) -> str:
            return "/".join(str(totals[m][metric]) for m in ("rules", "laya", "hybrid"))

        print(
            f"{name} ({len(cases)} cases, rules/laya/hybrid): fully correct "
            f"{trio('fully_correct')} · unsafe downgrades {trio('unsafe_downgrades')} · "
            f"missed danger {trio('missed_danger')} · false danger {trio('false_danger')}",
            flush=True,
        )
    ordered = sorted(all_latency)
    report["latency_ms"] = {
        "p50": round(statistics.median(ordered), 1),
        "p95": round(ordered[int(0.95 * (len(ordered) - 1))], 1),
        "n": len(ordered),
    }
    report["calibration_p_dangerous"] = calibration(all_cal)
    print(
        json.dumps(
            {k: report[k] for k in ("load_seconds", "latency_ms", "calibration_p_dangerous")}
        )
    )
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
