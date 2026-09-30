# Claude entry point

@AGENTS.md

Read `docs/agents/claude.md` and the current ready task in `docs/tasks.json`. See `docs/START-HERE.md` for launch prompts. Explicitly read each target directory's `AGENTS.md` before editing.

Claude owns specification, operator UX, frontend, intake prompts and independent review. Codex owns contracts, backend infrastructure and deterministic decision engines. Cross-agent coordination happens through merged commits, issues and `docs/handoffs/`, not shared chat memory.

Opus 5.5 availability is confirmed by the user. Use Opus 5.5 for architecture and independent review; use Sonnet for ordinary implementation. The architect and reviewer roles are pinned to `claude-opus-5-5`. Custom roles in `.claude/agents/` are available to invoke for the assigned task; their existence does not launch a team automatically. Keep one writing agent per worktree.
