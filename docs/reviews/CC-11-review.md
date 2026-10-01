# CC-11: Adversarial review and benchmark evaluation — 2026-09-30

- Reviewer: Claude (claude-opus-5-5), in the independent-review role. The same model family wrote the CC-04, CC-06 and CC-09 code, so this is not independent of those parts. Codex wrote the allocator and the planner under test.
- Code under test: branch `claude/cc-11-evaluation` at `e4d8a57` (clean tree). It is stacked on CC-10 (#27), CC-09 (#26) and the Codex stack (#21–#25).
- Machine: macOS 26.4.1 arm64, 10 CPUs, Python 3.12.14, OR-Tools 9.15.6755. The solver runs with 1 worker and seed 7.
- Everything is synthetic. Dispatch is simulated, and no network, model or routing key was used.

## 1. Allocation benchmark (100 seeds)

`cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100 --json ../evals/benchmark/results.json` (109 s).

**Method.** Each seed produces one 10-minute stream:

- 4–9 caller reports drawn from 17 synthetic texts (English and Hinglish) at routable random points in the demo area;
- a unit breakdown with probability 0.3;
- a road-closing flood polygon with probability 0.5.

The same stream runs through the real API twice: once with the production lexicographic CP-SAT allocator, and once with `allocate(..., baseline=True)`.

- The baseline is nearest-feasible greedy, with identical candidates, eligibility, reachable routes, capacities, locks and pins.
- After every world change the planner recomputes, the proposal is approved with all acknowledgements, and simulated dispatch is delivered.
- There are 714 replans per policy, with no harness errors.

| Metric (100 seeds) | CP-SAT planner | Nearest-eligible baseline | Paired (planner better / tie / baseline better) |
| --- | --- | --- | --- |
| Severity-weighted first-decision response time, mean of seeds | **757 s** | 830 s | 46 / 52 / 2 |
| Critical needs with first ETA ≤ 8 min (unmet = miss) | **117 / 940 (12.4 %)** | 100 / 940 (10.6 %) | 17 / 83 / 0 |
| Needs unmet at first decision | 510 | 514 | — |
| Unmet demand quanta, final plan (sum) | 528 | 530 | 2 / 98 / 0 |
| Reassignments of committed units | 90 (21 to higher severity) | **34** (22 to higher severity) | 1 / 52 / 47 |
| Mean uncovered reserve zone/resource pairs per replan | 1.194 | **1.155** | 3 / 90 / 7 |
| Replan wall time p50 / p95 | 34 / 114 ms | 28 / 89 ms | — |

Paired differences (baseline − planner), with a seeded bootstrap 95 % CI over seeds:

- weighted response **+73.5 s [54.2, 94.3]**;
- critical-under-8-min count per seed −0.17 [−0.25, −0.10], meaning the planner has more hits;
- reassignments −0.56 [−0.71, −0.42], meaning the planner has more churn.

**Interpretation.**

- The planner reliably shortens severity-weighted response and gets more critical needs under 8 minutes, and it never does worse than the baseline on that count.
- It leaves about the same demand unmet. In this regime demand exceeds the fleet: the fixture has 2 ALS units, and 90 % of generated needs are critical, so about half of all needs are unmet under either policy.
- The absolute percentages describe this stress set, not a city.
- The cost is churn. The planner moves committed units about 2.6× as often, and 69 of its 90 moves are lateral: to the same or lower severity, to save travel time. That is finding **F3**.

**Limits of the method:**

- Units do not advance along routes between events, so ETAs are measured from start positions.
- Near-arrival locks therefore rarely trigger.
- Latency includes the cached offline road router and is measured on this machine only. It is not a claim about scale.

## 2. Triage evaluation

`cd backend && uv run python ../evals/triage/run_eval.py --json ../evals/triage/report.json`

| Set | Fully correct | Unsafe downgrades | Missed danger | Over-triage | Category | Required escalations |
| --- | --- | --- | --- | --- | --- | --- |
| `cases.dev.jsonl` (lexicon was tuned on it) | 24/24 | 0 | 0 | 0 | 24/24 | 16/16 |
| `cases.heldout.jsonl` (CC-06, same author) | 30/30 | 0 | 0 | 0 | 30/30 | 19/19 |
| **`cases.cc11.jsonl` (new in CC-11, recorded before any fix)** | **18/30** | **0** | **6** | 0 | 25/30 | 8/11 |

The new set deliberately uses styles the lexicon never saw: SMS shorthand, typos, long rambling calls, Devanagari and Hinglish, abbreviations ("RTA at jn"), mid-sentence corrections and injection.

**No unsafe downgrade occurred.** Every miss left the fact `unknown`, and the assessment plans an unknown dangerous fact provisionally, so resources are not withheld. The harm is weaker escalation: three required `LIFE_THREAT_INDICATED` escalations did not fire (**F1**).

## 3. Adversarial probes (10)

`cd backend && uv run python ../evals/adversarial/run_probes.py --json ../evals/adversarial/results.json` → **9/10 passed**.

| Probe | Result |
| --- | --- |
| Approval with one acknowledgement missing | PASS, `409 UNACKNOWLEDGED_FLAGS` and nothing approved |
| 8 concurrent approvals of one plan | PASS: one 200, seven 409, exactly one `PlanApproved` |
| Approval after a unit status change | PASS, `409 STALE_PLAN` |
| Approval with a wrong session | PASS, `409 STALE_SESSION` |
| Idempotent retry, and key reuse with a changed body | PASS: replayed, then 422 |
| Dispatch after approval | PASS: 10 `SimulatedDispatchSent`, all with `simulated: true` |
| Replay: every prefix folds, head and restart hash-equal | PASS (67 prefixes) |
| Report-text canary in events, receipts or intake state | PASS, absent |
| Medical ID values in events or receipts after a grant | PASS, absent |
| BLS pinned to an ALS need returns `OVERRIDE_CONFLICT` with `TYPE_INELIGIBLE` | **FAIL**: `409 OVERRIDE_INFEASIBLE` with no `conflicts` (**F2**) |

The live console E2E runs (CC-09 and CC-10 handoffs, 17/17 and 18/18) cover the operator-facing races: an approval dialog voided by a breakdown, a stale approval, reconnect with backlog replay, and model failure.

## 4. Findings for CC-12, prioritised

| ID | Severity | Finding | Reproduction | Expected |
| --- | --- | --- | --- | --- |
| F1 | **High (release-blocking)** | Intake misses on unseen phrasing (details below). | `run_eval.py`, `cases.cc11.jsonl` | Missed life threats must escalate. Add the phrases, keep 0 unsafe downgrades, and re-label the set as tuned afterwards. |
| F2 | **High (release-blocking)** | Override rejections carry no coded reason (0004). This was review #21-1. | Probe `override_conflict_has_coded_reason` | `409 OVERRIDE_CONFLICT` with `conflicts[{code: UNIT_LOCKED \| TYPE_INELIGIBLE \| UNIT_NOT_AVAILABLE \| ROUTE_UNAVAILABLE \| CAPACITY_EXCEEDED \| DUPLICATE_UNIT_PIN \| CONTRADICTS_OVERRIDE, unit_id, detail}]`, and the same list in `OverrideRejected`. |
| F3 | Medium | Planner churn: 69 of 90 reassignments are lateral (travel-time) moves of committed units. The baseline makes 12. | Benchmark `reassignments` / `reassignments_to_higher_severity` | Lateral moves of en-route units should need a material saving. Re-measure: the response-time and critical gains must hold. |
| F4 | Medium | Unmet-need reasons conflate "no route" with "no capacity". | Demo water rescue; a benchmark point in Bellandur lake | `ROUTE_UNAVAILABLE` / `WATER_ACCESS_NOT_MODELLED` reason codes. The console must say "unreachable", not "no unit". |
| F5 | Medium (**fixed in this branch**) | A road-status question ("Is the underpass near Silk Board flooded?") became a high-severity water-rescue emergency: `assess()` upgraded information requests on `water_rising`. | `tests/test_intake_api.py::test_road_status_question_is_not_promoted_to_an_emergency` (fails before the fix) | Only fire or a caller in danger upgrades a road question, as in the intake rules. |
| F6 | Low | Routine calls over-triaged to emergency (details below). Conservative, but costs operator attention. | `cases.cc11.jsonl` r04, r07, r09, r24, r30 | Correct category, with no loss of upgrade on danger words. |
| F7 | Low | Near-arrival lock: the allocator locks on the current route ETA, while the post-solve gate checks the approved plan's ETA. This was review #21-2. It is not exercised here, because units do not move. | Code review of `lock_for` / `validate_capacity_and_locks` | One lock definition, shared by the allocator and the gate. |

F1 in detail: 6 missed dangers.

- r06, Hindi: «सीने में तेज़ दर्द», where the chest pain is split by an adjective.
- r11: "stuck on the third floor".
- r17: "someone under the debris".
- r21: "water still rising".
- r25: "following me with a knife".
- r15: a self-correction ("breathing, wait no, he stopped breathing"). This safely lands as a conflict and escalates, but the gold label is `no`.

F6 in detail:

- r04: tree on a parked car, nobody hurt.
- r09: flat battery.
- r07, r24, r30: road, traffic and power questions.

## 5. Not run

- Real Gemini, Laya or speech models (the CC-14 scope).
- Live ORS routing.
- Multi-hour runs, or load above 9 incidents per 10 minutes.
- Unit movement between events.

The triage sets are small and synthetic, and all are written by one model family. A new set written independently by people would be the next evidence step. Zero observed misses on a set is not a safety guarantee on real calls.
