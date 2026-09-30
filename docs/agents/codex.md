# Codex role

Own contracts, backend infrastructure, rules/solver/routing, integration and release fixes. Choose the model using `docs/MODELS.md`; the role does not require a hidden model override.

For each task: read merged dependencies and their handoffs; verify branch base; state owned paths; implement the task's acceptance criteria; run relevant checks; get Claude review; resolve findings; leave `docs/handoffs/CC-NN.md` and a PR with `Closes #N`.

When Claude's contract-ready UI lane runs in parallel, keep changes inside your owned paths. Treat `contracts/`, dependency manifests and root CI as shared integration points. A contract revision requires examples and regeneration plus a clear notice in the handoff.

Review Claude output for working behavior, accessibility, correct pending/stale approval states, model failures, schema drift and privacy boundaries. Do not rewrite the whole UI just to change style.
