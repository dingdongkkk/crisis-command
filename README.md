# Crisis Command

AI understands and explains. Rules and optimisation allocate. Humans approve risky changes.

An emergency-response **simulation and decision-support demo** for the GATEWAYS 2026 idea: synthetic Bengaluru incidents, flood-aware routing, resource allocation, plan diffs and an operator console.

**Status:** project setup, agent instructions and GitHub handoffs are ready. The application is not implemented yet. Begin with CC-01; do not mistake this repository's passing setup checks for an application test suite.

## Start here

1. Read [the build brief](docs/BRIEF.md) and [model assignments](docs/MODELS.md).
2. Follow [the agent sequence](docs/WORKFLOW.md). Tasks and acceptance criteria live in [tasks.json](docs/tasks.json).
3. Run `python3 scripts/taskboard.py` to see the current GitHub dependency queue (requires authenticated `gh`).
4. Give the first prompt in [START-HERE.md](docs/START-HERE.md) to Claude. Give the next ready Codex task to Codex when its prerequisites are merged.

GitHub: [private repository](https://github.com/dingdongkkk/crisis-command), [task issues](https://github.com/dingdongkkk/crisis-command/issues), [Actions](https://github.com/dingdongkkk/crisis-command/actions). Read [GitHub setup and enforcement limits](docs/GITHUB.md).

| Responsibility | Development agent |
| --- | --- |
| Product specification, operator UX, frontend, language prompts, independent QA | Claude Sonnet; Opus for difficult design/review if available |
| Contracts, backend, event log, rules, CP-SAT, routing, replanning, integration, CI | Codex Astra; Sol for routine implementation |
| Acceptance, demos, merging after review | You |

See [MODELS.md](docs/MODELS.md) for exact model guidance and the separate models used **inside** the app.

## Planned stack

Python 3.12, FastAPI, SQLite append-only events, OR-Tools CP-SAT, Shapely; React + TypeScript + Vite + Tailwind + Leaflet. Begin with deterministic fixtures and templates. Add a Gemini text adapter behind an interface; retain an offline fallback. LangGraph and Laya fine-tuning are optional after the core works.

## Checks available now

```sh
python3 scripts/validate_setup.py
python3 -m unittest discover -s tests -v
python3 scripts/taskboard.py --offline
```

Live board: `python3 scripts/taskboard.py`. Refresh labels: `python3 scripts/taskboard.py --sync` (writes GitHub issue status labels). GitHub Actions also refreshes them after issue changes and pushes to main. This does **not** start either AI subscription or auto-merge code.

## Repository map

- `AGENTS.md`, `CLAUDE.md`: shared working rules and Claude entry point.
- `docs/agents/`, `.claude/agents/`: ownership guides and Claude Code role definitions.
- `docs/WORKFLOW.md`, `docs/tasks.json`: dependency graph and completion criteria.
- `docs/ARCHITECTURE.md`, `contracts/README.md`: proposed architecture and contract checklist.
- `docs/handoffs/`: durable handoffs between agents.
- `backend/`, `frontend/`, `evals/`: scoped instructions for future implementation.
- `.github/`: CI, dependency labels, issue forms, PR template and code ownership.

Source: the user's *Crisis Command Ideation Round 1 2026* PDF. The original PDF is kept outside this repository; [BRIEF.md](docs/BRIEF.md) records the relevant requirements and the changes proposed for an achievable build.
