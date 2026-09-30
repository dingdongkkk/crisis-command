# Crisis Command

AI understands and explains. Rules and optimisation allocate. Humans approve risky changes.

An emergency-response **simulation and decision-support demo** for the GATEWAYS 2026 idea: synthetic Bengaluru incidents, flood-aware routing, resource allocation, plan diffs and an operator console.

**Status:** the demo is implemented end to end. That covers:

- a live operator console on MapLibre GL;
- an event-sourced FastAPI backend;
- rules-first multilingual intake;
- a flood-aware OpenStreetMap road router;
- lexicographic CP-SAT allocation;
- human approval, and simulated dispatch only.

Everything is synthetic, and this is **not** an emergency service.

## Run it

```sh
scripts/demo.sh        # needs uv and Node.js 22+; no API keys
```

Then open http://127.0.0.1:5321 and press **Advance to T+0**. Only the base-map tiles (OpenFreeMap) need the internet; intake, routing, planning and dispatch simulation run offline. The full guide covers setup on a clean machine, the demo walkthrough, data persistence, optional providers, the verification commands and troubleshooting: [docs/RUN-DEMO.md](docs/RUN-DEMO.md).

## Measured, not claimed

These results come from 100 seeded synthetic scenarios against a nearest-eligible baseline under identical constraints ([review](docs/reviews/CC-11-review.md), [results](evals/benchmark/results.json)):

- **Response:** the allocator shortens the severity-weighted first-decision response by about 9 %.
- **Critical needs:** it gets more critical needs under 8 minutes and is never worse on any seed.
- **Cost:** it reassigns committed units more often. Every reassignment is shown in the plan diff and needs human approval.
- **Safety of triage:** triage has produced zero unsafe downgrades on all labelled sets.

These are synthetic-scenario measurements, not clinical or city-scale claims.

## Development workflow

1. Read [the build brief](docs/BRIEF.md) and [model assignments](docs/MODELS.md).
2. Follow [the agent sequence](docs/WORKFLOW.md). Tasks and acceptance criteria live in [tasks.json](docs/tasks.json).
3. Run `python3 scripts/taskboard.py` to see the current GitHub dependency queue (requires authenticated `gh`).
4. Give the first prompt in [START-HERE.md](docs/START-HERE.md) to Claude. Give the next ready Codex task to Codex when its prerequisites are merged.

All 14 copy-paste task prompts plus review, repair, merge and resume prompts: [complete prompt workflow](docs/PROMPT-WORKFLOW.md).

GitHub: [private repository](https://github.com/dingdongkkk/crisis-command), [task issues](https://github.com/dingdongkkk/crisis-command/issues), [Actions](https://github.com/dingdongkkk/crisis-command/actions). Read [GitHub setup and enforcement limits](docs/GITHUB.md).

| Responsibility | Development agent |
| --- | --- |
| Product specification, operator UX, frontend, language prompts, independent QA | Claude Opus 5.5 for specification/review; Sonnet for routine UI/intake |
| Contracts, backend, event log, rules, CP-SAT, routing, replanning, integration, CI | Codex Astra; Sol for routine implementation |
| Acceptance, demos, merging after review | You |

See [MODELS.md](docs/MODELS.md) for exact model guidance and the separate models used **inside** the app.

## Stack

Python 3.12, FastAPI, SQLite append-only events with replay, OR-Tools CP-SAT, and an offline OpenStreetMap road graph (ODbL). The console is React 19, TypeScript and Vite, with MapLibre GL and OpenFreeMap tiles. The Gemini text adapter is optional and has a rules-only fallback. Laya and speech are evaluated separately in CC-14.

## Checks

All of these run in CI; the exact list is in [RUN-DEMO.md](docs/RUN-DEMO.md#5-verification-commands).

```sh
python3 scripts/validate_setup.py && python3 -m unittest discover -s tests
cd backend && uv run ruff check . && uv run mypy && uv run pytest && uv run python -m app.scenario
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

Task board: `python3 scripts/taskboard.py` (needs an authenticated `gh`).

## Repository map

- `AGENTS.md`, `CLAUDE.md`: shared working rules and Claude entry point.
- `docs/agents/`, `.claude/agents/`: ownership guides and Claude Code role definitions.
- `docs/WORKFLOW.md`, `docs/tasks.json`: dependency graph and completion criteria.
- `docs/ARCHITECTURE.md`, `contracts/README.md`: proposed architecture and contract checklist.
- `docs/handoffs/`: durable handoffs between agents.
- `backend/`, `frontend/`, `evals/`: the application, the console and the evaluation harnesses, each with scoped instructions.
- `scripts/demo.sh`: one-command local demo.
- `.github/`: CI, dependency labels, issue forms, PR template and code ownership.

Source: the user's *Crisis Command Ideation Round 1 2026* PDF. The original PDF is kept outside this repository; [BRIEF.md](docs/BRIEF.md) records the relevant requirements and the changes proposed for an achievable build.
