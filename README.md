# Crisis Command

**AI understands and explains. Rules and optimisation allocate. Humans approve risky changes.**

Crisis Command is an emergency-response **simulation and decision-support console** for a flood night in Bengaluru. Synthetic callers report emergencies in English, Hindi and Hinglish. The system extracts the facts, plans which units go where over a real road network, explains why, and waits for a human to approve before anything is "dispatched". Dispatch is simulated.

> ⚠️ **Simulation only.** Everything is synthetic data. There are no real calls, no real dispatch and no notifications. This is not a validated emergency-dispatch system.

**Live demo:** https://crisis-command-tau.vercel.app. This is the full system: the console runs on Vercel and the backend (API, planner, live feed) runs on Render at `crisis-command-api.onrender.com`. The backend is on a free plan, so the first load after it has been idle can take up to a minute, and its data resets when it restarts. To run it on your own computer, see [Run it](#run-it).

---

## Features

### Operator console

- **Live city map** (MapLibre GL, OpenStreetMap streets) with incidents, units, flood zones, reserve-coverage zones, approved routes (solid) and proposed routes (dashed). It has an **expand-map** mode (button or the `M` key).
- **Incident queue**, sorted by severity and then waiting time. Each incident shows its critical / high severity and tags such as `PROVISIONAL` or `ALS UNMET`.
- **Situation strip**: emergencies, critical incidents, units free, units out of service, unmet needs and uncovered zones.
- **Plan panel**: the proposed plan is clearly marked **"PROPOSED — not dispatched"**. It shows what changed (added, moved, released units), the unmet needs with plain-language reasons, and the flags you must acknowledge before approving.
- **Reinforcements by road**: the fastest road route from every unit to the selected incident.
- **Timeline** of incidents from T+0 to T+10, plus keyboard shortcuts (`j`/`k` to move between incidents, `a` to approve, `o` to override, `?` for help).
- **Live connection badge**: Live, Disconnected or Resyncing. Commands are disabled when the data might be stale, and missed events are replayed after a reconnect.

### Caller intake (triage)

- **Rules-first multilingual extraction**: English, Hindi (Devanagari) and Hinglish. Each fact (breathing, conscious, bleeding, trapped, fire, gas, water rising and so on) is **yes / no / unknown, with the exact words as evidence**.
- **Unknown is never treated as "no"**: an unknown critical fact is planned for as a *provisional* need.
- **Targeted follow-up questions**, which you answer with Yes / No / Not sure from the triage panel.
- **Escalation to a human**: on a life threat, when the caller asks for a person, on conflicting facts, or on critical uncertainty.
- **Optional AI model (Gemini)**: it can only *raise* risk, never lower it. If it fails, intake falls back to rules with a visible "model unavailable" banner. Prompt-injection text is never sent to the model.

### Planning and dispatch

- **Lexicographic CP-SAT optimiser** (Google OR-Tools). It minimises unmet critical, then high, medium and low demand, then waiting time, then travel and operating cost. It also keeps reserve units covering each zone.
- **Flood-aware road router** on a recorded OpenStreetMap graph of Bengaluru (17k nodes). Flooded roads close, and an unreachable incident says "unreachable" instead of showing a made-up ETA.
- **Hard safety rules**:
  - no double-booking;
  - no ineligible units (a BLS ambulance never "counts" as ALS, except through an explicit bridge);
  - a unit on scene or about to arrive is never pulled away;
  - hospital and shelter capacity is respected.
- **Human approval**: approval is bound to the exact plan version. If the world changes while you're reading, the approval is refused ("Plan changed — nothing approved").
- **Operator overrides**: pin, hold, forbid, a BLS bridge for an ALS shortage, or downgrade a provisional need. Refusals say exactly why (`UNIT_LOCKED`, `TYPE_INELIGIBLE`, `ROUTE_UNAVAILABLE` and so on).
- **Duplicate reports**: two callers reporting the same emergency are flagged. The operator links them (their demand merges) or keeps them separate; nothing merges automatically.
- **Medical ID (synthetic)**: shown only with consent, only if the caller is the patient, only for an active incident, and only with a reason. Every attempt is audited, and the values never enter the log.
- **Simulated dispatch**: a dispatch is cancelled if its road floods after approval.

### Reliability and audit

- **Event-sourced backend**: every change is an idempotent event in SQLite, and replaying the log reproduces the exact state.
- **Scripted scenario** for T+0 → T+2 → T+5 → T+10: cardiac call, accident, gas leak, a flooded car reported twice, a school roof collapse, and an ambulance breakdown.
- **Measured, not claimed**: on 100 seeded scenarios against a "nearest free unit" baseline, the planner reaches critical needs faster: **117 vs 100** of 940 critical needs within 8 minutes, and never worse on any seed. The details and limits are in [`docs/demo/CLAIMS.md`](docs/demo/CLAIMS.md).

---

## Run it

### 1. Install the tools (once)

| Tool | Why | Install |
| --- | --- | --- |
| **git** | get the code | <https://git-scm.com/downloads> (preinstalled on macOS) |
| **uv** | runs the Python backend; it also installs Python 3.12 for you | macOS: `brew install uv` · macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` · Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| **Node.js 22+** | runs the console | <https://nodejs.org/> (LTS) |

### 2. Get the code and start everything

```bash
git clone https://github.com/dingdongkkk/crisis-command.git
cd crisis-command
scripts/demo.sh
```

The script installs the exact locked dependencies (the first run takes a minute or two), then starts the backend and the console:

```
Operator console  http://127.0.0.1:5321
API docs          http://127.0.0.1:8321/docs
```

Open **http://127.0.0.1:5321**. Press **Ctrl-C** in the terminal to stop.

- **Port already in use?** Pick others: `BACKEND_PORT=8400 CONSOLE_PORT=5400 scripts/demo.sh`
- **Start from a clean database:** `scripts/demo.sh --fresh`
- **No API keys are needed.** Everything runs offline except the background map tiles.

**Windows:** run the two commands from "Run the pieces separately" below in two terminals. `demo.sh` is a bash script; it also works under WSL or Git Bash.

### 3. Try the demo (5 minutes)

1. Click **Advance to T+0**. Three calls arrive: a cardiac emergency, a road question and a flat tyre. Only the first is an emergency.
2. Click the cardiac incident. The **Triage** panel shows each fact, the words it came from, and that the caller asked for a human.
3. In **Plan**, tick every "I understand" box, then click **Approve & dispatch (simulated)**. The routes turn solid: **DISPATCHED (simulated)**.
4. Click **Advance to T+2**, then **T+5**. On the second flooded-car report, use **Resolve… → Same emergency — link**.
5. Click **Advance to T+10**. An ambulance breaks down, and the plan states plainly which critical needs cannot be met.
6. Try these too:
   - **Simulated call**: type your own report in English, Hindi or Hinglish.
   - **Medical ID** on the cardiac incident: confirm the caller is the patient, enter `mprof_syn_0001` and give a reason.
   - **Override…** to see coded refusals.
   - **↻ Reset** to start again.

The full 8-minute presenter script is in [`docs/demo/SCRIPT.md`](docs/demo/SCRIPT.md).

### Run the pieces separately (any OS)

```bash
# terminal 1: backend API on :8321
cd backend
uv sync --frozen
uv run uvicorn app.main:app --host 127.0.0.1 --port 8321

# terminal 2: console on :5321 (proxies /api to the backend)
cd frontend
npm ci
CRISIS_BACKEND_URL=http://127.0.0.1:8321 npm run dev -- --host 127.0.0.1 --port 5321
```

On Windows PowerShell, set the variable first: `$env:CRISIS_BACKEND_URL="http://127.0.0.1:8321"; npm run dev -- --port 5321`.

**Console without a backend** (built-in demo data): open `http://127.0.0.1:5321/?mock=demo`.

---

## Tests and evaluations

```bash
# backend: lint, types, 211 tests, contract check, scripted scenario with replay check
cd backend && uv run ruff check . && uv run mypy && uv run pytest && uv run python -m app.scenario

# triage evaluation (fails if any critical fact is ever marked "safe" without evidence)
cd backend && uv run python ../evals/triage/run_eval.py

# adversarial probes: approval races, stale approvals, replay, privacy, overrides
cd backend && uv run python ../evals/adversarial/run_probes.py

# 100-seed allocation benchmark (about 2 minutes)
cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100

# frontend: lint, types, 53 tests, production build
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

CI runs all of these on every push (`.github/workflows/ci.yml`).

---

## How it's built

| Part | Technology |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLite append-only event store, WebSocket live feed |
| Planning | Google OR-Tools CP-SAT (lexicographic objective), deterministic fallback |
| Routing | Recorded OpenStreetMap road graph of Bengaluru (© OpenStreetMap contributors, ODbL), A* with flood closures |
| Intake | Rules-based multilingual extraction; optional Gemini adapter |
| Console | React 19, TypeScript, Vite, MapLibre GL with OpenFreeMap tiles |
| Contracts | JSON Schema, with generated TypeScript types and OpenAPI (`contracts/`) |

```
backend/    API, event store, intake, planner, router, tests
frontend/   operator console (React)
contracts/  shared JSON Schema + OpenAPI
evals/      triage sets, benchmark, adversarial probes
docs/       decisions, demo pack, reviews, handoffs
scripts/    demo.sh (one-command start), setup checks
```

More documentation:

- [`docs/RUN-DEMO.md`](docs/RUN-DEMO.md): detailed run guide and troubleshooting.
- [`docs/demo/`](docs/demo/): presentation script, claims and evidence, fallback runbook.
- [`docs/decisions/`](docs/decisions/): the design decisions behind triage, allocation, overrides and approvals.
- [`docs/reviews/CC-11-review.md`](docs/reviews/CC-11-review.md): independent review and benchmark.

## Limitations

- Synthetic data only. ETAs use a recorded road graph with assumed speeds, not live traffic.
- Water rescue routes are not modelled, and the system says so.
- There is no login; run it on your own machine (localhost).
- The background map tiles need the internet; everything else works offline.
- The hosted demo has no login and is shared: anyone with the link can advance or reset the scenario. Its free hosting is slow and sleeps when idle.
- Not a medical or dispatch product.

Built for GATEWAYS 2026 with AI coding agents (Claude and Codex). See [`docs/WORKFLOW.md`](docs/WORKFLOW.md).
