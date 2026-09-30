# CC-12: Resolve CC-11 findings and package the demo (Claude)

- Author: Claude (claude-opus-5-5). The user authorised Claude to take Codex tasks. This builds on Codex's preparation, `docs/handoffs/CC-12.md` / #25.
- Branch and PR: `claude/cc-12-release` (#30), stacked on CC-11 (#28). The PR body carries `Closes #12`.
- Reviewer: Codex/Astra — pending. Status: ready for review.

## Findings resolved (`docs/reviews/CC-11-review.md`)

| ID | Resolution | Coverage |
| --- | --- | --- |
| F1 (blocking) intake misses | Phrase families added: Hindi/Hinglish chest pain with an intensifier, trapped on a floor or under debris, water still rising, threats or hiding, "N of us". The held-out score was 18/30 before the fix and 29/30 after tuning, with 0 unsafe downgrades and 11/11 escalations. The set is now labelled a regression set. The remaining self-correction case escalates as a visible conflict. | `evals/triage/cases.cc11.jsonl`, run in CI |
| F2 (blocking) overrides without reasons | The preflight `app/planning/override_checks.py` returns `409 OVERRIDE_CONFLICT` with coded `conflicts[]` per 0004. The same list is recorded in `OverrideRejected`. | `tests/test_override_conflicts.py`; probes 10/10 |
| F3 planner churn | **Measured, not changed.** Raising the reassignment cost from 600 to 1800 cut reassignments from 90 to 56, but response rose from 757 to 799 s and critical-under-8 fell from 117 to 107. The moves buy response time and each needs human approval. This is a product decision for the user. | benchmark |
| F4 unmet reasons | `NO_REACHABLE_UNIT` and `WATER_ACCESS_NOT_MODELLED`, with console text. Reachability is probed only for needs with no candidate. A first version raised replan p95 to about 1.3 s; it was fixed before commit. | backend and `labels.test.ts` |
| F5 road question promoted to an emergency | Fixed in CC-11 | regression test |
| F6 over-triage of routine calls | Breakdown and road/power-question families added; negated "no fire". Categories are 30/30. | triage set |
| F7 lock definition | The gate uses the allocator's `lock_for` on the current route, in both the allocator and the approval path. | `test_gate_uses_the_allocators_current_route_lock` |

## Packaging

- `scripts/demo.sh`: one command, no keys. It starts the API on 8321 and the console on 5321, checks tools and ports, and `--fresh` starts a new database.
- `docs/RUN-DEMO.md`: setup on a clean machine, walkthrough, persistence, providers and drills, verification and troubleshooting.
- README, `.env.example` and `docs/RUN-BACKEND-DEMO.md` updated (the last now points to RUN-DEMO).
- CI now also runs:
  - lint of `evals/`;
  - the scenario with replay equality;
  - the triage evaluation;
  - the probes;
  - a 3-seed benchmark smoke run.

## Verification (clean commit `208d17d`, 2026-10-01)

| Check | Outcome |
| --- | --- |
| Setup checks | passed |
| Backend ruff, format and mypy | passed |
| Backend `pytest` | 206 passed |
| Contracts and generated types | current |
| `app.scenario` | replay-equal |
| Triage | dev 24/24, held-out 30/30, CC-11 29/30; 0 unsafe downgrades in every set |
| Probes | 10/10 |
| Frontend lint, typecheck, test and build | passed, 53 tests |
| Benchmark (100 seeds, `evals/benchmark/results.json`) | decision metrics identical to CC-11; replan p50/p95 40/127 ms on macOS arm64 |
| Live end-to-end run | 17/17 on the default backend, 18/18 on the model-failure drill (`docs/screenshots/cc-12/`) |
| `scripts/demo.sh` | started and was served on test ports |

Not run:

- GitHub CI for this branch (pending on the PR);
- real Gemini or ORS keys;
- an install on another machine or on Linux.

## Limitations

- Units don't move in the benchmark.
- Water navigation is not modelled.
- ETAs use assumed speeds.
- There is no authentication; bind to localhost.
- The base-map tiles need the internet.
- All triage sets are synthetic.

## Handoff

Next: CC-13 (demo narrative). Merge the stack #15 → #30 in order after review.

## Addendum: P1 findings from the Codex whole-code review (PR #32)

Codex's console PR (#29) reported four P1 backend issues without a reproduction in the repository. Each is reproduced here by a test that fails on the previous code and passes now (`backend/tests/test_p1_fixes.py`):

| P1 | Fix |
| --- | --- |
| Medical consent crossed a session reset (incident IDs restart per session) | Profiles store `linked_session_id`. A link is to (session, incident); anything else is `PROFILE_NOT_LINKED`. The demo seed carries the session. |
| A confirmed life threat did not escalate an informational incident | `assess` counts established dangerous values even when the fact wasn't applicable to the first classification, and a confirmed life threat upgrades any category. Confirmation records `IncidentCategoryChanged` (reason `CONFIRMED_DANGER`) and `EscalatedToHuman`. |
| Linking a duplicate dropped a critical need only the second caller reported | Linking first merges the candidate's demand into the original: max quantity per type, the stronger basis, the higher severity. It is replay-equal. |
| A queued simulated dispatch was sent after a flood closed its road | Before delivery the route is recomputed under the current closures, outside the writer lock. If it is not drivable, or if the closures change during delivery, the command is cancelled with `ROUTE_INVALIDATED`. The replan proposes a new route for approval. |

Verification:

- Backend: 211 passed; ruff, format and mypy clean.
- Scenario: replay-equal.
- Triage: unchanged, 0 unsafe downgrades.
- Probes: 10/10.
- Frontend: 53 passed.
- Live end-to-end run: 17/17 (`docs/screenshots/cc-12-p1/`).

Known remaining gap: if the merged original is later re-assessed from its own intake (an answer or confirmation), `assess` rebuilds needs from the original's facts only. Carrying merged demand through re-assessment needs a merge record, and is future work.
