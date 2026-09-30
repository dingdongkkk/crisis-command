# Complete copy-paste prompt workflow

Repository: https://github.com/dingdongkkk/crisis-command

Use Claude Code and Codex with access to this repository. Select the model in the app before pasting; naming a model inside a prompt does not switch the main session. Claude Opus 5.5 access is confirmed by the user. These prompts do not require you to launch custom subagents.

For the simplest first build, run CC-01 through CC-13 in numerical order. After each task, perform the review/fix/merge cycle below before starting its successor. CC-14 is optional. You can instead parallelize CC-03 and CC-04 after CC-02, and later CC-06 with the Codex decision-engine lane, in separate worktrees with no shared-file writes. Never let two agents write to one checkout at once.

Start a fresh task/session per implementation issue. A fresh reviewer session helps it assess the code independently. Use the same repository, merged handoffs and actual commit IDs instead of copying long chat histories.

Claude web fallback: attach relevant repository instructions, task criteria and current source files; request proposed Markdown/code artifacts and clearly unrun checks. Have Codex import those artifacts on the implementation branch, run checks and arrange review before merge. The copy-paste implementation prompts below assume repository/terminal/GitHub access; they cannot make Claude web edit local files by themselves.

## Loop after every implementation prompt

1. The author returns the PR URL, commit SHA, test evidence and a handoff file.
2. Send the review prompt below to the **other** agent: Claude Opus 5.5 reviews Codex; Codex Astra reviews Claude.
3. If findings remain, paste the review into the original author's session with the repair prompt. Have the reviewer check the new implementation commit.
4. When review and CI pass, send the merge prompt to the agent with repository access. It checks the reviewed version and merges.
5. Only after the prerequisite issues close as completed, run the next implementation prompt. GitHub labels track readiness; they do not launch agents.

### Review prompt (replace all angle-bracket fields)

```text
Independently review Crisis Command PR <PR_URL> for <TASK_ID> at implementation
commit <COMMIT_SHA>. Read AGENTS.md, scoped instructions, docs/tasks.json,
and the task's handoff. Inspect the actual diff and run relevant checks in an
isolated review checkout; preserve any existing implementation worktree.

Check acceptance criteria, contract compatibility, unit/resource invariants,
triage uncertainty, stale approvals, replay, failure states and UI behavior
where relevant. Do not rewrite the implementation during review and do not
start another task. For each actionable finding, give severity, file/location,
expected and actual behavior, and a reproduction or missing regression test.

Return the exact reviewed commit, checks run, checks not run, blocking findings,
and a concise review result that I can paste back to the author. If there are
no blockers, say so explicitly; do not invent defects or claim independent
human GitHub approval. For a review-report task, review the methodology and
reproducibility; findings assigned to the next repair task are expected.
```

### Repair prompt (send to the original author)

```text
Address the following review of your current Crisis Command task and PR.
Verify each finding against the code. Fix valid findings, add focused regression
coverage, and explain with evidence any finding you disagree with. Keep the
same task branch and scope. Run relevant checks and update the handoff with
the original review's author and reviewed commit, fixes, and remaining gaps.
Push the update and return the new implementation commit SHA for re-review.
Do not merge or start the next task yet.

Review findings:
<PASTE_REVIEW_HERE>
```

### Merge and handoff prompt (after review passes)

```text
Finish Crisis Command task <TASK_ID>, PR <PR_URL>. The independent review of
implementation commit <REVIEWED_COMMIT_SHA> is pasted below. Verify the current
PR belongs to this task, its prerequisites are completed, its acceptance
criteria and handoff are complete, and all required CI checks passed.
Verify no implementation changes occurred after the reviewed commit; if they
did, request re-review rather than merging an unreviewed version. Review any
subsequent handoff-only documentation changes for accuracy.

If there are no blockers, squash-merge this PR into main and verify its linked
issue closes as completed. Preserve local work and update the local base only
where safe. Refresh the taskboard, then return the merge commit, next ready
task IDs, assigned models, and the next copy-paste prompt. Do not launch another
agent or begin the next implementation automatically. If blocked, report the
specific unmet check rather than bypassing it.

Independent review:
<PASTE_PASSING_REVIEW_HERE>
```

Private branch protection is unavailable on the current GitHub plan, so these checks are a working procedure rather than server-enforced protection. See [GITHUB.md](GITHUB.md).

## Implementation prompts

Each block is self-contained: copy the whole block for that task. The model and prerequisites are given immediately above it. Check live readiness with `python3 scripts/taskboard.py`.

### CC-01 — Finalize MVP specification and operator flow

Model: **Claude Opus 5.5**. Starts after: **none; this is the first task**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/1).

```text
Work only on CC-01: Finalize MVP specification and operator flow in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: none; this is the first task. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: docs/BRIEF.md, docs/ARCHITECTURE.md, contracts/README.md, docs/decisions/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Review the draft architecture and record decisions for unknown triage facts, conflicting overrides, ALS shortage and hard versus soft reserve rules.
2. Define screen states and acceptance scenarios for intake, plan diff, approval, override and replay.
3. Publish entity/event/API examples with coordinate, time, capacity, idempotency and stale-version semantics. Codex reviews implementation feasibility.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-01.md using the template.
Commit and push, then open a PR with Closes #1. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-02 (codex); check their other prerequisites.
```

### CC-02 — Create runnable scaffold and canonical contracts

Model: **Codex Astra, medium reasoning**. Starts after: **CC-01**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/2).

```text
Work only on CC-02: Create runnable scaffold and canonical contracts in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-01. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/, frontend/, contracts/, .github/workflows/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Create Python 3.12 FastAPI and React/TypeScript/Vite apps with pinned lockfiles and exact setup commands.
2. Implement canonical models and generate JSON Schema/OpenAPI and TypeScript consumers with valid/invalid contract tests.
3. Add backend lint/type/test and frontend lint/type/test/build CI jobs; health endpoint and frontend smoke check pass from a clean install.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-02.md using the template.
Commit and push, then open a PR with Closes #2. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-03 (codex), CC-04 (claude); check their other prerequisites.
```

### CC-03 — Build event store and synthetic world state

Model: **Codex Astra, medium reasoning**. Starts after: **CC-02**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/3).

```text
Work only on CC-03: Build event store and synthetic world state in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-02. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/storage/, backend/app/domain/, backend/app/api/, evals/fixtures/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Append idempotent events transactionally and project incidents, fleet, facilities, flood state and plan versions.
2. Provide state snapshot, event replay, WebSocket sequence and reconnect protocol plus seeded synthetic Bengaluru data.
3. Test duplicate commands, concurrent version checks, restart/replay equivalence and simulation reset boundaries.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-03.md using the template.
Commit and push, then open a PR with Closes #3. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-05 (codex), CC-06 (claude); check their other prerequisites.
```

### CC-04 — Build operator console against contract mocks

Model: **Claude Sonnet 5.5**. Starts after: **CC-02**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/4).

```text
Work only on CC-04: Build operator console against contract mocks in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-02. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: frontend/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Implement map, incident queue, fleet, triage facts, plan diff, policy flags and approval/override screens using schema-valid mocks.
2. Cover keyboard interaction, loading/empty/error/disconnected states and clear proposed versus approved simulation status.
3. Add UI interaction tests and screenshots at desktop and narrow widths; show required map attribution.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-04.md using the template.
Commit and push, then open a PR with Closes #4. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-06 (claude), CC-09 (claude); check their other prerequisites.
```

### CC-05 — Implement assessment and constrained allocation

Model: **Codex Astra, high reasoning**. Starts after: **CC-03**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/5).

```text
Work only on CC-05: Implement assessment and constrained allocation in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-03. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/domain/, backend/app/planning/, evals/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Implement versioned assessment/needs rules, waiting-age priority and integer-scaled CP-SAT objectives.
2. Enforce membership, availability, resource type, one task per unit, route reachability, facility capacity and locks; retain explicit unmet demand.
3. Test shortage, zero fleet, equal-cost ties, infeasible overrides, unavailable locked units and solver timeout; return structured reasons and solver status.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-05.md using the template.
Commit and push, then open a PR with Closes #5. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-07 (codex); check their other prerequisites.
```

### CC-06 — Implement typed text intake and safe explanations

Model: **Claude Sonnet 5.5**. Starts after: **CC-03, CC-04**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/6).

```text
Work only on CC-06: Implement typed text intake and safe explanations in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-03, CC-04. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/intake/, evals/triage/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Implement template/rule adapters and an optional Gemini adapter behind merged interfaces; no API key required for the default demo.
2. Extract yes/no/unknown facts with evidence, ask targeted questions and escalate human requests/critical uncertainty independent of model success.
3. Validate schema, timeouts and prompt-injection cases; derive explanations only from validated facts. Add held-out English/Hindi/Hinglish examples with no silent critical-to-no conversions.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-06.md using the template.
Commit and push, then open a PR with Closes #6. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-09 (claude); check their other prerequisites.
```

### CC-07 — Implement flood-aware routing and capacity inputs

Model: **Codex Astra, medium reasoning**. Starts after: **CC-05**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/7).

```text
Work only on CC-07: Implement flood-aware routing and capacity inputs in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-05. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/routing/, backend/app/domain/, evals/routing/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Build fixture and ORS Directions adapters with explicit seconds/metres, bounded calls and cache invalidation by flood version.
2. Check routes against closure polygons and facility reachability; never treat no-route or provider failure as an ordinary road ETA.
3. Test polygon crossings, isolated incidents/facilities, stale cache, tow-to-emergency upgrade inputs and boat eligibility.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-07.md using the template.
Commit and push, then open a PR with Closes #7. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-08 (codex); check their other prerequisites.
```

### CC-08 — Wire replanning policy gate and simulated dispatch

Model: **Codex Astra, high reasoning**. Starts after: **CC-07**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/8).

```text
Work only on CC-08: Wire replanning policy gate and simulated dispatch in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-07. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/planning/, backend/app/api/, backend/app/storage/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Connect event changes through impact analysis, locks, routes, allocation, invariant validation and versioned plan diffs.
2. Bind approve/override to plan and event version in a transaction; implement idempotent simulated outbox and watchdog feedback.
3. Test breakdown plus new critical incident, late approvals, conflicting overrides, duplicate dispatch, replay without resend and visible unmet ALS/reserve flags.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-08.md using the template.
Commit and push, then open a PR with Closes #8. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-09 (claude); check their other prerequisites.
```

### CC-09 — Integrate console and intake with the live backend

Model: **Claude Sonnet 5.5**. Starts after: **CC-04, CC-06, CC-08**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/9).

```text
Work only on CC-09: Integrate console and intake with the live backend in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-04, CC-06, CC-08. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: frontend/, backend/app/intake/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Replace screen mocks with the real API, intake and WebSocket stream using generated types.
2. Demonstrate report to plan to operator decision to simulated dispatch; why-not results reference actual solver facts.
3. Add end-to-end tests for reconnect/sequence gaps, stale approvals, model failure and the breakdown scenario. Coordinate backend fixes with Codex.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-09.md using the template.
Commit and push, then open a PR with Closes #9. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-10 (codex); check their other prerequisites.
```

### CC-10 — Add Medical ID duplicate reports and scenario runner

Model: **Codex Astra, medium reasoning**. Starts after: **CC-09**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/10).

```text
Work only on CC-10: Add Medical ID duplicate reports and scenario runner in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-09. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/, evals/, frontend/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Implement synthetic opt-in profiles with caller-is-patient check, active-incident access and audited reads; separate profiles from immutable event payloads.
2. Add spatial/time duplicate candidate blocking and optional E5 similarity while preserving conflict/provenance and distinct incidents.
3. Implement deterministic T+0/T+2/T+5/T+10 scenario runner, hospital matching and simulated pre-alerts; wire required UI controls after Claude lane is merged.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-10.md using the template.
Commit and push, then open a PR with Closes #10. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-11 (claude); check their other prerequisites.
```

### CC-11 — Run adversarial review and benchmark evaluation

Model: **Claude Opus 5.5**. Starts after: **CC-10**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/11).

```text
Work only on CC-11: Run adversarial review and benchmark evaluation in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-10. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: evals/, docs/reviews/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Independently run and record 100 seeded scenarios against a nearest eligible available-unit baseline with identical constraints.
2. Report weighted response time, critical-under-eight-minute share, unmet needs, reassignments, uncovered zones and p50/p95 replanning latency with machine/commit metadata.
3. Run held-out triage tests and approval/replay/privacy failure cases; deliver reproducible prioritized findings for Codex. Complete the review task even if it finds defects; CC-12 is the repair gate.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-11.md using the template.
Commit and push, then open a PR with Closes #11. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-12 (codex); check their other prerequisites.
```

### CC-12 — Resolve review findings and package the demo

Model: **Codex Astra, high reasoning**. Starts after: **CC-11**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/12).

```text
Work only on CC-12: Resolve review findings and package the demo in Crisis Command.
Read AGENTS.md, docs/agents/codex.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-11. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/, frontend/, evals/, .github/, docs/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Fix all release-blocking CC-11 findings with regression coverage; Claude verifies repairs at the final commit.
2. Provide clean-machine setup and run instructions, persistent data behavior, simulated dispatch boundaries and no-key offline fixtures.
3. Pass full application CI and the scripted scenario, document remaining limitations and measured performance. No public deployment is required.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-12.md using the template.
Commit and push, then open a PR with Closes #12. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-13 (claude); check their other prerequisites.
```

### CC-13 — Prepare demo narrative and release acceptance

Model: **Claude Sonnet 5.5**. Starts after: **CC-12**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/13).

```text
Work only on CC-13: Prepare demo narrative and release acceptance in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-12. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: docs/demo/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Write a timed presentation script showing T+0 through T+10, plan diff, approval/override and offline fallback.
2. Prepare claims/evidence table, screenshots and fallback runbook; distinguish measured outcomes from hypotheses.
3. User can reproduce the complete demo from documented commands and decides whether to publish/deploy.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-13.md using the template.
Commit and push, then open a PR with Closes #13. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: CC-14 (claude); check their other prerequisites.
```

### CC-14 — Evaluate optional Laya and voice extensions

Model: **Claude Opus 5.5 for experiment design; Sonnet for routine implementation**. Starts after: **CC-13**. [GitHub issue](https://github.com/dingdongkkk/crisis-command/issues/14).

```text
Work only on CC-14: Evaluate optional Laya and voice extensions in Crisis Command.
Read CLAUDE.md, AGENTS.md, docs/agents/claude.md, scoped AGENTS.md files,
docs/BRIEF.md, docs/WORKFLOW.md, this task in docs/tasks.json, its GitHub issue,
and all merged dependency handoffs. Verify readiness with the live taskboard.
Prerequisites: CC-13. If unmet, report the blocker and stop this task.

Use a new task branch based on current main, with a separate worktree if another
agent is active. Preserve existing changes. Claim the issue as status:doing.
Owned paths: backend/app/intake/, evals/triage/, docs/experiments/. Coordinate shared-contract changes.

Deliver all of these acceptance criteria:
1. Only after core acceptance: pin Laya checkpoint/license, measure hardware latency, evaluate held-out triage recall/calibration and compare to baseline.
2. If time permits, benchmark multilingual Whisper/browser speech with text fallback; select a local LLM only after memory/latency checks.
3. Keep new adapters optional and disabled by default until tests justify adoption; record negative results without blocking the completed core demo.

Run the applicable checks and report their exact results, including anything
not run. Keep the default demo reproducible without paid API calls; no real
dispatch or medical data. Save docs/handoffs/CC-14.md using the template.
Commit and push, then open a PR with Closes #14. Move the issue to
status:review. Return the PR URL, implementation commit SHA, checks, remaining
limitations and a ready-to-paste review prompt for the other agent. Do not merge
your own work or start a successor in this implementation turn.
Successors after reviewed merge: none; report experiment results; check their other prerequisites.
```

## Resume after a break

```text
Resume Crisis Command coordination. Read AGENTS.md and docs/PROMPT-WORKFLOW.md.
Run the live taskboard and inspect relevant open PRs and recent handoffs.
Tell me which task is in review, needs repairs, or is ready next, with the
correct agent/model and its exact prompt. Do not infer completion from old
chat messages or offline taskboard output, close unfinished issues, or launch
multiple writing agents in one worktree.
```
