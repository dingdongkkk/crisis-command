# Claude entry point

@AGENTS.md

Read `docs/agents/claude.md` and the current ready task in `docs/tasks.json`. See `docs/START-HERE.md` for launch prompts. Explicitly read each target directory's `AGENTS.md` before editing.

Claude owns specification, operator UX, frontend, intake prompts and independent review. Codex owns contracts, backend infrastructure and deterministic decision engines. Cross-agent coordination happens through merged commits, issues and `docs/handoffs/`, not shared chat memory.

Use Sonnet for ordinary implementation. Use Opus for difficult architecture/review only if your `/model` picker exposes it; Sonnet is the fallback. Custom roles in `.claude/agents/` are available to invoke for the assigned task; their existence does not launch a team automatically. Keep one writing agent per worktree.
