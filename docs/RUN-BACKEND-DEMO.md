# Running the Codex backend demo

This stack contains unmerged prerequisites. Use `codex/cc-12-package-prep` to inspect the combined result. Do not use the root Claude checkout for Codex edits.

## Setup

Install Python 3.12 and uv, then from the repository:

```sh
cd backend
uv sync --frozen
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

No API keys are needed. SQLite defaults to `backend/data/crisis.db`, persists across restarts, and is selected with `DATABASE_PATH`. Open http://127.0.0.1:8000/docs for typed endpoints. All mutations require a UUIDv4 `Idempotency-Key` and the current `expected_session_id` from `GET /state`. Retries reuse the same key and identical body. Reset retains old audit history and command receipts; it creates a new session and cancels pending old-session deliveries.

## Reproducible backend acceptance run

In another terminal:

```sh
cd backend
uv run python -m app.scenario --output ../evals/scenario-smoke.json
```

This uses a disposable database and the recorded OpenStreetMap road graph. It runs T+0, T+2, T+5 and T+10, explicitly acknowledges flags as a synthetic test operator, delivers only simulated commands, and compares replayed and stored state. The live API never automatically grants an operator approval. A1 is held on scene after T+2; A2 breaks down at T+10. Unmet ALS, reserve and water-rescue demand remain visible.

For a manually operated run use `/demo/advance`, inspect `/state`, then `/plans/{plan_id}/approve` with the displayed version/sequence and required flag IDs. World changes invalidate stale approvals. Commands and WebSocket delivery share the same SQLite event source.

## Boundaries and recovery

- The frontend still uses Claude's mocks. CC-09 must wire the API/WebSocket client; this runbook does not claim an end-to-end live UI.
- Bind to localhost: no authentication or production deployment is configured.
- Profile data and report text are in separate revocable tables; profile values do not enter events or receipts. `PUT /medical-profiles/{ref}` with `consent_granted: false` erases profile values. Profile access requires explicit caller-is-patient and an active incident, and is audited.
- ORS is optional: `ROUTING_PROVIDER=ors_directions` plus server-side `ORS_API_KEY`. Missing keys/errors produce unavailable routes. Default `fixture` uses recorded roads and assumed demo speeds, not measured traffic ETAs. Water navigation is unavailable; no road route is substituted for a boat.
- Keep `LLM_PROVIDER=template`; optional Gemini extraction is not connected to this API yet. Selecting Gemini emits a degraded health flag.
- Restart resumes pending simulated delivery with revision fences; replay is read-only and cannot resend. Database contention returns 503 and requires same-key retry.
- To start a clean disposable run, use the scenario command. Preserve a persistent database if its history matters; `/demo/reset` is the normal reset control.

Validation and incomplete release gates are recorded in `docs/reviews/codex-delivery.md`.
