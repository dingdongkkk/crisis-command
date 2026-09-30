# GitHub setup

Created 2026-09-30 under the authenticated account `dingdongkkk`.

- Repository: https://github.com/dingdongkkk/crisis-command (private).
- Default branch: `main`; local `origin` tracks this repository.
- Squash merging enabled; merge commits and rebase merging disabled; merged branches auto-delete.
- Fourteen issues with agent, scope and dependency-status labels; mapping in `.github/task-map.json`.
- CODEOWNERS lists the repository owner. No teammates have been invited.
- Repository checks and agent-handoff Actions use GitHub's token; no LLM API secrets are required.
- The original PDF and local PDF renders are not committed.

## Enforcement limitation

GitHub returned HTTP 403 when branch protection was requested: this account must upgrade to GitHub Pro or make the repository public to enable that feature. The repository remains private. Required checks, mandatory PRs, review and no-force-push rules are therefore **working conventions, not server-enforced branch protection**. CODEOWNERS does not enforce review by itself.

Before every merge, check the PR tests and the independent agent review. No plan upgrade or visibility change was made. If branch protection becomes available, require PRs, the `setup-checks` check (and application checks added in CC-02), up-to-date branches and resolved conversations; disallow force pushes/deletions. Agent reviews made under one human account are not separate human approvals.

## Operations

```sh
python3 scripts/taskboard.py          # Read current readiness
python3 scripts/taskboard.py --sync   # Reconcile managed status labels
```

To recreate missing setup on the same configured repository, inspect `docs/tasks.json` and `.github/task-map.json`, then run `python3 scripts/bootstrap_github.py --apply`. It creates missing labels/issues and reuses known task IDs/titles; it does not rewrite existing issue content. If dependencies change, update the manifest and the affected issue descriptions together.

The handoff workflow runs on managed-state-relevant issue events or main manifest/script changes. Labels changed by GitHub Actions' own token do not recursively launch a model. Manual label changes can retrigger reconciliation. `status:doing` and `status:review` persist only while prerequisites are complete. To return work to ready, remove both labels; the workflow recalculates readiness.

To refresh without changing an issue, run **Agent handoffs → Run workflow** in the Actions UI. Its job summary shows the next ready tasks. Starting Claude or Codex remains a manual action using `docs/START-HERE.md`.
