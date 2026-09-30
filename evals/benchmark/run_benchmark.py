#!/usr/bin/env python3
"""CC-11 allocation benchmark: lexicographic CP-SAT planner vs nearest-eligible baseline.

Each seed generates one synthetic 10-minute incident stream (reports through the real rules
intake, unit breakdowns, flood road closures). The *same* stream is replayed through the real
command path twice — once with the production allocator, once with ``allocate(baseline=True)``
(nearest feasible unit, identical eligibility, reachability, capacity, locks and pins). After
every world change the planner recomputes, the proposal is approved with all acknowledgements
and simulated dispatch is delivered. Nothing leaves the process; no network, no API key.

    cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100 \\
        --json ../evals/benchmark/results.json
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as app_main  # noqa: E402
import app.planning.service as planning_service  # noqa: E402
from app.planning.allocator import allocate  # noqa: E402
from app.routing.service import RouteService  # noqa: E402
from app.storage.event_store import EventStore  # noqa: E402

CRITICAL_TARGET_S = 480  # "critical under eight minutes"
RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
BOX = ((77.57, 12.93), (77.68, 13.02))  # inside the routed OSM extract, around the fleet

# Synthetic caller texts by family (distinct from the triage evaluation sets). The intake,
# not this table, decides severity and needs.
TEMPLATES: list[str] = [
    "My father has severe chest pain and is sweating, he is conscious",
    "Chest pain, not breathing normally, please hurry",
    "Old man collapsed on the footpath, not breathing",
    "Road accident, bike and car, one person bleeding heavily",
    "Accident on the flyover, two people injured, one trapped in the car",
    "Bus hit an auto, three people hurt, lots of bleeding",
    "Fire in the kitchen of an apartment, smoke everywhere, people inside",
    "Shop is on fire, someone is trapped upstairs",
    "Strong gas smell in the building, we are evacuating 15 people",
    "Wall collapsed at a construction site, workers trapped",
    "Water rising fast, our car is stuck, 2 people inside",
    "Someone fainted at the metro station, conscious now but very weak",
    "Accident hua hai, ek aadmi ka bahut khoon beh raha hai",
    "Aag lagi hai, dhuan bahut hai, andar log hain",
    "Seene mein dard hai, saans lene mein taklif",
    "Flat tyre near the signal, nobody hurt",
    "Is the underpass near Silk Board flooded?",
]


@dataclass
class Scenario:
    seed: int
    events: list[dict[str, Any]]


def generate(seed: int, reachable: Any = lambda _: True) -> Scenario:
    """Seeded stream. ``reachable`` rejects points no unit can drive to (lakes, off-graph):
    they are handled safely as unmet (no ETA) but would measure routing, not allocation."""
    rng = random.Random(seed)
    events: list[dict[str, Any]] = []
    for _ in range(rng.randint(4, 9)):
        for _attempt in range(50):
            lon = round(rng.uniform(BOX[0][0], BOX[1][0]), 5)
            lat = round(rng.uniform(BOX[0][1], BOX[1][1]), 5)
            if reachable((lon, lat)):
                break
        events.append(
            dict(
                kind="report",
                t=rng.randrange(0, 600, 10),
                text=rng.choice(TEMPLATES),
                at=[lon, lat],
            )
        )
    if rng.random() < 0.3:
        unit = rng.choice(["unit_A1", "unit_A2", "unit_B1", "unit_B2", "unit_F1"])
        events.append(dict(kind="breakdown", t=rng.randrange(60, 600, 10), unit=unit))
    if rng.random() < 0.5:
        lon, lat = rng.uniform(77.59, 77.66), rng.uniform(12.94, 13.00)
        w, h = rng.uniform(0.004, 0.012), rng.uniform(0.004, 0.010)
        ring = [[lon, lat], [lon + w, lat], [lon + w, lat + h], [lon, lat + h], [lon, lat]]
        ring = [[round(x, 5), round(y, 5)] for x, y in ring]
        events.append(dict(kind="flood", t=rng.randrange(0, 600, 10), ring=ring))
    order = {"flood": 0, "breakdown": 1, "report": 2}
    events.sort(key=lambda e: (e["t"], order[e["kind"]]))
    return Scenario(seed, events)


@dataclass
class Run:
    policy: str
    seed: int
    latencies_ms: list[float] = field(default_factory=list)
    first_decision: dict[str, dict[str, Any]] = field(default_factory=dict)
    reassignments: int = 0
    reassignments_to_higher_severity: int = 0
    uncovered_per_step: list[int] = field(default_factory=list)
    final_unmet: int = 0
    plans: int = 0
    errors: list[str] = field(default_factory=list)


def _post(client: TestClient, path: str, body: dict[str, Any]) -> Any:
    return client.post(path, json=body, headers={"Idempotency-Key": str(uuid.uuid4())})


def run_policy(scenario: Scenario, policy: str, routes: RouteService, workdir: Path) -> Run:
    result = Run(policy, scenario.seed)
    store = EventStore(workdir / f"{policy}-{scenario.seed}.db")
    store.ensure_session()
    planning_service.allocate = partial(allocate, baseline=policy == "baseline")  # type: ignore[attr-defined]
    app_main.RouteService = lambda **_: routes  # type: ignore[assignment,misc]
    app = app_main.create_app(store=store, auto_plan=False)
    weights = store.state().policy.severity_weights
    previous: dict[str, str] = {}
    with TestClient(app) as client:
        planner = app.state.planner
        sid = store.active_session()
        for e in scenario.events:
            if e["kind"] == "report":
                r = _post(
                    client,
                    "/reports",
                    dict(
                        expected_session_id=sid,
                        channel="text_sim",
                        text=e["text"],
                        location={"type": "Point", "coordinates": e["at"]},
                        location_source="fixture",
                        sim_time_s=e["t"],
                    ),
                )
            elif e["kind"] == "breakdown":
                r = _post(
                    client,
                    f"/units/{e['unit']}/status",
                    dict(expected_session_id=sid, to_status="broken_down", sim_time_s=e["t"]),
                )
            else:
                r = _post(
                    client,
                    "/flood-events",
                    dict(
                        expected_session_id=sid,
                        flood_id=f"flood_s{scenario.seed}",
                        version=1,
                        closes_roads=True,
                        effective_sim_time_s=e["t"],
                        geometry={"type": "Polygon", "coordinates": [e["ring"]]},
                    ),
                )
            if r.status_code >= 400:
                result.errors.append(
                    f"{e['kind']}@{e['t']}: {r.status_code} {r.json().get('code')}"
                )
                continue
            started = perf_counter()
            planner.recompute()
            result.latencies_ms.append((perf_counter() - started) * 1000)
            state = store.state()
            plan = state.current_proposal
            if plan is not None:
                r = _post(
                    client,
                    f"/plans/{plan.plan_id}/approve",
                    dict(
                        expected_session_id=sid,
                        expected_plan_version=plan.version,
                        expected_planning_sequence=plan.based_on_planning_sequence,
                        acknowledged_flag_ids=[f.flag_id for f in plan.flags if f.requires_ack],
                    ),
                )
                if r.status_code != 200:
                    result.errors.append(f"approve: {r.status_code} {r.json().get('code')}")
                planner.deliver()
            state = store.state()
            approved = state.approved_plan
            if approved is None:
                continue
            result.plans += 1
            severity = {i.incident_id: i.severity.value for i in state.incidents}
            served = {a.need_id: a for a in approved.assignments if a.need_id and a.satisfies_need}
            active_needs = [
                (i, n) for i in state.incidents if i.status == "active" for n in i.needs
            ]
            for inc, need in active_needs:
                if need.need_id in result.first_decision:
                    continue
                a = served.get(need.need_id)
                result.first_decision[need.need_id] = dict(
                    severity=severity[inc.incident_id],
                    weight=weights[severity[inc.incident_id]],
                    type=need.type,
                    eta_s=a.eta_s if a else None,
                )
            now = {a.unit_id: a.need_id or a.bridges_need_id or "" for a in approved.assignments}
            active_ids = {n.need_id for _, n in active_needs}
            need_rank = {
                n.need_id: RANK[i.severity.value] for i in state.incidents for n in i.needs
            }
            for unit, need_id in previous.items():
                # Reassigned: a committed unit moved to different work while its need is open.
                if need_id in active_ids and now.get(unit) not in (None, need_id):
                    result.reassignments += 1
                    if need_rank.get(now[unit] or "", 9) < need_rank.get(need_id, 9):
                        result.reassignments_to_higher_severity += 1
            previous = now
            result.uncovered_per_step.append(
                sum(1 for c in approved.coverage if c.status != "covered")
            )
        final = store.state().approved_plan
        result.final_unmet = sum(n.quantity_unmet for n in final.unmet_needs) if final else 0
    return result


def summarize(run: Run) -> dict[str, Any]:
    decisions = list(run.first_decision.values())
    served = [d for d in decisions if d["eta_s"] is not None]
    critical = [d for d in decisions if d["severity"] == "critical"]
    weight = sum(d["weight"] for d in served)
    return dict(
        needs=len(decisions),
        weighted_response_s=round(sum(d["weight"] * d["eta_s"] for d in served) / weight, 1)
        if weight
        else None,
        critical_needs=len(critical),
        critical_under_8min=sum(
            1 for d in critical if d["eta_s"] is not None and d["eta_s"] <= CRITICAL_TARGET_S
        ),
        first_decision_unmet=sum(1 for d in decisions if d["eta_s"] is None),
        final_unmet_quanta=run.final_unmet,
        reassignments=run.reassignments,
        reassignments_to_higher_severity=run.reassignments_to_higher_severity,
        mean_uncovered_zones=round(statistics.fmean(run.uncovered_per_step), 3)
        if run.uncovered_per_step
        else 0.0,
        replans=len(run.latencies_ms),
        latencies_ms=[round(x, 1) for x in run.latencies_ms],
        errors=run.errors,
    )


def pct(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    k = (len(ordered) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo), 1)


def aggregate(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    runs = [r[policy] for r in rows]
    crit = sum(r["critical_needs"] for r in runs)
    wrt = [r["weighted_response_s"] for r in runs if r["weighted_response_s"] is not None]
    lat = [x for r in runs for x in r["latencies_ms"]]
    return dict(
        seeds=len(runs),
        needs=sum(r["needs"] for r in runs),
        weighted_response_s_mean=round(statistics.fmean(wrt), 1) if wrt else None,
        weighted_response_s_median=round(statistics.median(wrt), 1) if wrt else None,
        critical_needs=crit,
        critical_under_8min=sum(r["critical_under_8min"] for r in runs),
        critical_under_8min_share=round(sum(r["critical_under_8min"] for r in runs) / crit, 4)
        if crit
        else None,
        first_decision_unmet=sum(r["first_decision_unmet"] for r in runs),
        final_unmet_quanta=sum(r["final_unmet_quanta"] for r in runs),
        reassignments=sum(r["reassignments"] for r in runs),
        reassignments_to_higher_severity=sum(r["reassignments_to_higher_severity"] for r in runs),
        mean_uncovered_zones=round(statistics.fmean(r["mean_uncovered_zones"] for r in runs), 3),
        replans=len(lat),
        replan_ms_p50=pct(lat, 0.5),
        replan_ms_p95=pct(lat, 0.95),
        runs_with_errors=sum(1 for r in runs if r["errors"]),
    )


def paired(rows: list[dict[str, Any]], key: str, lower_is_better: bool = True) -> dict[str, int]:
    out = {"planner_better": 0, "tie": 0, "baseline_better": 0}
    for r in rows:
        a, b = r["planner"][key], r["baseline"][key]
        if a is None or b is None or a == b:
            out["tie"] += 1
        elif (a < b) == lower_is_better:
            out["planner_better"] += 1
        else:
            out["baseline_better"] += 1
    return out


def bootstrap_mean_diff(rows: list[dict[str, Any]], key: str, n: int = 5000) -> dict[str, Any]:
    """Paired baseline - planner difference with a seeded percentile bootstrap 95% CI."""
    diffs = [
        r["baseline"][key] - r["planner"][key]
        for r in rows
        if r["planner"][key] is not None and r["baseline"][key] is not None
    ]
    if not diffs:
        return {}
    rng = random.Random(0)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return dict(
        pairs=len(diffs),
        mean=round(statistics.fmean(diffs), 2),
        ci95=[round(means[int(0.025 * n)], 2), round(means[int(0.975 * n) - 1], 2)],
    )


def metadata() -> dict[str, Any]:
    def git(*args: str) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"

    import os

    import ortools

    return dict(
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        commit=git("rev-parse", "HEAD"),
        dirty=bool(git("status", "--porcelain", "--untracked-files=no")),
        python=platform.python_version(),
        ortools=ortools.__version__,
        platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor() or "unknown",
        cpu_count=os.cpu_count(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--first-seed", type=int, default=1)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    routes = {"planner": RouteService(), "baseline": RouteService()}
    rows = []
    with tempfile.TemporaryDirectory(prefix="crisis-bench-") as tmp:
        probe = EventStore(Path(tmp) / "probe.db")
        probe.ensure_session()
        world = probe.state()
        checker = RouteService()

        def reachable(point: tuple[float, float]) -> bool:
            return any(
                checker.route(world, u.position.coordinates, point).route_status == "ok"
                for u in world.units
            )

        for seed in range(args.first_seed, args.first_seed + args.seeds):
            scenario = generate(seed, reachable)
            row: dict[str, Any] = {"seed": seed, "events": len(scenario.events)}
            # Alternate order so warm route caches do not favour one policy.
            order = ("planner", "baseline") if seed % 2 else ("baseline", "planner")
            for policy in order:
                row[policy] = summarize(run_policy(scenario, policy, routes[policy], Path(tmp)))
            rows.append(row)
            p, b = row["planner"], row["baseline"]
            print(
                f"seed {seed:3d}: needs {p['needs']:2d} · wrt {p['weighted_response_s']} vs "
                f"{b['weighted_response_s']} s · crit<8 {p['critical_under_8min']}/"
                f"{p['critical_needs']} vs {b['critical_under_8min']}/{b['critical_needs']} · "
                f"unmet {p['final_unmet_quanta']} vs {b['final_unmet_quanta']}",
                flush=True,
            )
    report = dict(
        benchmark="cc-11-allocation-v1",
        simulated=True,
        definitions=dict(
            weighted_response_s="severity-weighted mean ETA of the first approved decision per "
            "need (served needs only)",
            critical_under_8min_share="critical needs whose first approved ETA <= 480 s; unmet "
            "counts as a miss",
            first_decision_unmet="needs left unmet in the first approved plan that contained them",
            final_unmet_quanta="unmet demand quanta in the last approved plan",
            reassignments="committed units moved to a different need while their need stayed open",
            mean_uncovered_zones="mean per replan of reserve zone/resource pairs not covered",
            replan_ms="wall time of Planner.recompute (state read, candidate routing, solve, "
            "publish)",
        ),
        metadata=metadata(),
        summary=dict(planner=aggregate(rows, "planner"), baseline=aggregate(rows, "baseline")),
        paired=dict(
            weighted_response_s=paired(rows, "weighted_response_s"),
            critical_under_8min=paired(rows, "critical_under_8min", lower_is_better=False),
            final_unmet_quanta=paired(rows, "final_unmet_quanta"),
            reassignments=paired(rows, "reassignments"),
            mean_uncovered_zones=paired(rows, "mean_uncovered_zones"),
        ),
        baseline_minus_planner=dict(
            weighted_response_s=bootstrap_mean_diff(rows, "weighted_response_s"),
            critical_under_8min=bootstrap_mean_diff(rows, "critical_under_8min"),
            reassignments=bootstrap_mean_diff(rows, "reassignments"),
        ),
        seeds=rows,
    )
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["paired"], indent=2))
    print(json.dumps(report["baseline_minus_planner"], indent=2))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
