# Start the project

The repo is a planning and collaboration setup, not a running application yet.

## 1. Start Claude on CC-01

Use Claude Code from this folder, signed in with your Claude account. This setup did not find the `claude` executable on PATH, so it has not tested your Claude login or model access. Follow the [official setup guide](https://code.claude.com/docs/en/setup) if you need to install it. Check `/model`; use Opus for CC-01 if available, otherwise Sonnet.

Paste:

```text
Work on CC-01 in this Crisis Command repository. Read CLAUDE.md, AGENTS.md,
docs/BRIEF.md, docs/ARCHITECTURE.md, docs/WORKFLOW.md, contracts/README.md
and CC-01 in docs/tasks.json. Check the live taskboard and use a new branch.
Finalize the MVP specification, operator screen states and contract decisions.
Resolve the documented ALS shortage, reserve, triage uncertainty and stale
approval questions with concrete examples and acceptance criteria. Keep this
bounded to CC-01. Save docs/handoffs/CC-01.md, run the setup checks and open a
PR linked to the task issue. Return a Codex review prompt and the PR URL.
```

Claude web alternative: attach the relevant Markdown files and request the same specification as Markdown. Have Codex commit that artifact to a CC-01 branch and arrange review. Claude web cannot be assumed to edit or run this local repo.

## 2. Review before handing implementation to Codex

Give the opposite agent this prompt, filling in the actual PR and commit:

```text
Independently review PR <URL> at commit <SHA> for task <CC-NN>.
Read AGENTS.md, the task acceptance criteria and its handoff. Inspect the diff,
run relevant checks and report only actionable issues with reproductions.
Check contracts, failure states and the product invariants. Do not rewrite the
implementation during review. Record which commit was reviewed and whether
blocking findings remain so the author can repair them before merge.
```

An agent's review is not a distinct human GitHub approval. Merge after the relevant checks and findings are resolved, according to the repository's available protection controls.

## 3. Start Codex on CC-02 after CC-01 merges

Choose Astra for the initial scaffold/contracts (medium reasoning is sufficient to start).

```text
Implement CC-02 from docs/tasks.json. Read AGENTS.md, docs/agents/codex.md,
the merged CC-01 handoff and contract decisions. Verify CC-01 is completed in
the live taskboard, create a new branch from updated main, and build the
runnable FastAPI/Python 3.12 and React/TypeScript/Vite skeleton with canonical
schemas, generated consumer types, lockfiles and real application CI. Fulfill
all CC-02 acceptance criteria without building later features. Run the checks,
save docs/handoffs/CC-02.md and open a PR linked to the task issue. Return a
Claude review prompt and the next tasks that become ready after merge.
```

## 4. Continue any ready task

```text
Work on <CC-NN> only. Read the shared and scoped instructions, docs/tasks.json,
and all prerequisite handoffs. Check the live taskboard before starting.
Use a separate branch/worktree and stay inside the task's ownership boundary.
Implement the acceptance criteria, run relevant checks, leave a handoff and
open a PR with Closes #<issue>. Request review by the other agent, resolve
findings, and state the next agent/task after merge. Do not start blocked work.
```

`python3 scripts/taskboard.py` shows the owner and issue for every task; `--offline` is only the all-not-started initial graph. You do not need to copy whole chat histories: the merged contract and handoff are the context.
