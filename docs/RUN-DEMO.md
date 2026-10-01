# Running Crisis Command

Everything here runs on one machine with **synthetic data and simulated dispatch only**. After installation only the base-map tiles (OpenFreeMap) use the internet; without them the console draws on a blank style. No command sends a real call, SMS, radio message, emergency-service request or family notification.

## 1. Clean-machine setup

Requirements:

- macOS or Linux
- Python 3.12 via [uv](https://docs.astral.sh/uv/getting-started/installation/) (uv installs the right Python itself)
- Node.js 22 or newer
- git

For the optional browser end-to-end run, Google Chrome.

```sh
git clone https://github.com/dingdongkkk/crisis-command.git
cd crisis-command
scripts/demo.sh
```

`demo.sh` does the following:

- Installs the locked dependencies (`uv sync --frozen`, and `npm ci` on first run).
- Starts the API on `127.0.0.1:8321` and the console on `127.0.0.1:5321`.
- Prints both URLs.

Ctrl-C stops both. Change the ports with `BACKEND_PORT=… CONSOLE_PORT=… scripts/demo.sh`. The script refuses ports that are already in use.

To run the pieces by hand:

```sh
cd backend && uv sync --frozen && uv run uvicorn app.main:app --host 127.0.0.1 --port 8321
cd frontend && npm ci && CRISIS_BACKEND_URL=http://127.0.0.1:8321 npm run dev -- --host 127.0.0.1 --port 5321
```

## 2. The demo in the console

1. Open http://127.0.0.1:5321. The badge reads **Live · seq N**.
2. **Advance to T+0 … T+10** plays the seeded Bengaluru scenario:
   - T+0: a cardiac call, a road question and a flat tyre.
   - T+2: an accident with bleeding, and a gas leak evacuation.
   - T+5: a flood-stranded car, reported twice.
   - T+10: unit A2 breaks down and a school roof collapses.
3. The right panel shows **PROPOSED vN — not dispatched**, with flags:
   - Tick every "I understand" box.
   - **Approve & dispatch (simulated)** asks for confirmation.
   - The plan then shows **DISPATCHED (simulated)**, and the map draws approved routes solid.
4. Try these from the console:
   - **Simulated call**: type English, Hindi or Hinglish caller text and pick a place.
   - **Pending question**: answer Yes, No or Not sure in the triage panel.
   - **Resolve…**: on the duplicate flood report, link it or keep it separate.
   - **Medical ID**: on the cardiac incident, confirm the caller is the patient, then enter `mprof_syn_0001` and a reason. The values are synthetic.
   - **Override…**: pin, hold, forbid or bridge. A refusal lists each broken constraint.
   - **Reset**: starts a new session. The old history is kept for audit.

`?mock=demo` runs the same console on built-in fixtures, with no backend. Use it as a fallback if the API cannot start.

## 3. Data and persistence

- **Database.** Events, projections, receipts and private tables live in one SQLite file:
  - `backend/data/crisis.db` by default, or `DATABASE_PATH`.
  - It persists across restarts.
  - `scripts/demo.sh --fresh` starts a new file and keeps old ones.
- **Append-only log.** Every state change is an idempotent event, and replay reproduces state.
- **Private tables.** Report text, intake dialogue state and Medical ID values live in separate private tables and never enter events or receipts. Revoking consent erases the profile values.
- **Reset.** `/demo/reset` creates a new session, cancels the old session's pending simulated deliveries, and keeps the history.
- **Commands.** Every command needs a UUIDv4 `Idempotency-Key` and the current `expected_session_id`. Retries reuse the same key and body.

## 4. Providers: offline by default

| Setting | Default | Optional | Behaviour when unavailable |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | `template` (rules only) | `gemini` + `GEMINI_API_KEY` | Rules-only intake, a `ModelAdapterDegraded` event, `/health.degraded = [MODEL_UNAVAILABLE]` and a console banner. Critical uncertainty escalates to an operator. |
| `ROUTING_PROVIDER` | `fixture` (recorded OSM road graph, assumed speeds) | `ors_directions` + `ORS_API_KEY` | The route is unavailable, with no ETA. Unmet needs say `NO_REACHABLE_UNIT`. |

Keys are read server-side only. The model is called outside the database write lock, and suspected prompt injection is never sent to it.

**Model-failure drill, with no external call:**

```sh
LLM_PROVIDER=gemini GEMINI_API_KEY=synthetic-drill-key GEMINI_ENDPOINT=http://127.0.0.1:9 scripts/demo.sh
```

Water navigation is not modelled. Water rescue stays unmet with `WATER_ACCESS_NOT_MODELLED`, and a road route is never substituted.

## 5. Verification commands

| What | Command |
| --- | --- |
| Setup checks | `python3 scripts/validate_setup.py && python3 -m unittest discover -s tests` |
| Backend | `cd backend && uv sync --frozen && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest && uv run python -m app.contracts.export --check` |
| Frontend | `cd frontend && npm ci && npm run lint && npm run typecheck && npm test && npm run build` |
| Scripted scenario T+0 → T+10, with replay equality | `cd backend && uv run python -m app.scenario` |
| Triage evaluation (fails on an unsafe downgrade) | `cd backend && uv run python ../evals/triage/run_eval.py` |
| Adversarial probes | `cd backend && uv run python ../evals/adversarial/run_probes.py` |
| 100-seed allocation benchmark (about 2 min) | `cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100 --json ../evals/benchmark/results.json` |
| Live browser end-to-end run (Chrome, both servers running) | `node frontend/scripts/e2e-live.mjs http://127.0.0.1:5321 http://127.0.0.1:8321 /tmp/e2e` |

CI runs everything above except the full benchmark (a 3-seed smoke run instead) and the browser end-to-end run.

## 6. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Badge says **Disconnected** | The API is down or unreachable. The console keeps the last data and disables commands. Restart the API; the console resubscribes and replays missed events. |
| "Port … is in use" | Choose other ports: `BACKEND_PORT=8400 CONSOLE_PORT=5400 scripts/demo.sh`. |
| Blank map, incidents still listed | The vector tiles (OpenFreeMap) are unreachable. The console states that the base map is unavailable, and incidents, routes and flood still draw on a blank style. |
| `Idempotency-Key must be a UUIDv4` | Only for manual API calls. Send `Idempotency-Key: $(uuidgen \| tr A-Z a-z)`. |
| Want a clean slate | Use **Reset** in the console, or `scripts/demo.sh --fresh`. |

## 7. Boundaries

- This is not a validated emergency dispatch system and is not for real incidents.
- There is no authentication. The operator identity is a configured synthetic operator, so bind to localhost only.
- ETAs come from a recorded road graph with assumed speeds, not measured traffic.
- Triage phrases are a demonstration lexicon, and model confidence is not a calibrated probability.
- Measured results and their limits are in `docs/reviews/CC-11-review.md` and `docs/handoffs/CC-12.md`.
