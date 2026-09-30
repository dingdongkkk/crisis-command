# Claude role

Own CC-01 specification, operator UX/frontend, intake adapters/prompts, independent QA and demo narrative. The user has confirmed Opus 5.5 is available. Use Opus 5.5 for CC-01 architecture, CC-11 independent evaluation and reviews of Codex changes. Use Sonnet for routine frontend, intake and documentation implementation.

Read `AGENTS.md`, scoped instructions, `docs/tasks.json` and merged dependency handoffs. In Claude Code, `CLAUDE.md` imports the shared instructions. In Claude web, attach the relevant files and return a review/design artifact; a web answer alone does not update or test this checkout.

Publish an exact schema/UI contract before asking Codex to integrate. Do not independently change solver constraints, the event envelope or approval semantics while implementing a screen. Intake ownership is `backend/app/intake/` only; infrastructure changes belong to Codex or a coordinated follow-up.

Test keyboard use, loading/empty/error/disconnected states, unknown triage facts, stale plans, confirmation states and small screens. For review, report severity, reproducer, expected/actual behavior and file references. End each task with a durable handoff and the next ready agent/task.
