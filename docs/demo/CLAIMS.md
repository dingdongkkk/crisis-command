# Claims and evidence

Say only what is in the **Measured** column. Everything is synthetic. Numbers come from the files cited, at the commits recorded in them.

## Measured

| Claim | Evidence | How to reproduce |
| --- | --- | --- |
| Against a nearest-eligible-unit baseline, under identical constraints, on 100 seeded synthetic 10-minute scenarios: <ul><li>the severity-weighted first-decision response is **757 s vs 830 s**, a paired mean difference of 73.5 s with bootstrap 95 % CI [54, 94];</li><li>the planner is better on 46 seeds, tied on 52 and worse on 2.</li></ul> | `evals/benchmark/results.json` (commit `208d17d`); `docs/reviews/CC-11-review.md` | `cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100` |
| Critical needs reached within 8 minutes: **117 vs 100 of 940**. The planner is never worse on any seed. | same | same |
| The planner reassigns committed units more often: **90 vs 34**, of which 21 vs 22 move to a higher severity. Every reassignment is shown in the plan diff and needs human approval. | same | same |
| Replanning takes **40 ms median and 127 ms at p95**, at 4–9 incidents with 9 units, on a macOS arm64 laptop with 1 solver worker. | same | same |
| **0 unsafe downgrades** in all labelled triage sets (dev 24, CC-06 held-out 30, CC-11 30). A critical fact is never predicted "safe" without words that establish it. | `evals/triage/report.json` | `cd backend && uv run python ../evals/triage/run_eval.py` |
| On a set of 30 phrasings the rules had never seen, the first result was **18/30** fully correct, with 6 missed dangers left as "unknown". After tuning it is 29/30, and the set is now a regression set, not a held-out one. | `docs/reviews/CC-11-review.md` | same |
| 10 of 10 adversarial probes pass. They cover: <ul><li>approvals with a missing acknowledgement;</li><li>8 concurrent approvals of one plan, with one winner;</li><li>stale and wrong-session approvals;</li><li>idempotency;</li><li>simulated-only dispatch;</li><li>replay of every event prefix;</li><li>report text and Medical ID values never appearing in the log;</li><li>override conflict reasons.</li></ul> | `evals/adversarial/results.json` | `uv run python ../evals/adversarial/run_probes.py` |
| The live console end-to-end run passes 17/17 checks (18/18 with a simulated model outage). It covers: <ul><li>a breakdown during an approval;</li><li>a stale approval;</li><li>reconnect with backlog replay;</li><li>duplicates;</li><li>Medical ID;</li><li>a simulated call;</li><li>reset.</li></ul> | `docs/screenshots/cc-12-p1/e2e-results.json` | `node frontend/scripts/e2e-live.mjs <console> <api> <out>` |
| Every state change is an idempotent event, and replaying the log reproduces the state exactly. | 211 backend tests; `app.scenario` replay check | `cd backend && uv run pytest && uv run python -m app.scenario` |

## Design properties (true by construction, tested)

- No automatic dispatch. Every plan waits for a human approval bound to its version and event sequence.
- Unknown critical facts stay `unknown`, never silently `no`, and are planned as provisional needs.
- A unit on scene, transporting or about to arrive is never reassigned.
- A missing route produces "unreachable" with no ETA. Water access is not modelled, and the system says so.
- A model failure degrades to rules-only intake with a visible banner. The model is never called while the database is locked.

## Hypotheses (not measured, do not state as results)

- That the planner would help real Bengaluru dispatchers.
- That the rules lexicon generalises to real callers.
- That ETAs reflect real traffic: speeds are assumed.
- Any clinical benefit.
- Performance at city scale.

## Known limitations

- Units do not move along their routes in the benchmark.
- Water navigation is not modelled.
- There is no authentication; run on localhost only.
- The OpenFreeMap base map needs the internet.
- All triage sets are synthetic and written by models.
- Merged duplicate demand is not carried through a later re-assessment.

**This is not a validated emergency dispatch system.**
