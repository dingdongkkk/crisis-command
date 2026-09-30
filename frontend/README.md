# Frontend

React + TypeScript + Vite. Node version in `.nvmrc`; dependencies pinned exactly in `package-lock.json`.

```sh
cd frontend
npm ci                 # clean install from the lockfile
npm run gen:contracts  # regenerate src/generated/contracts.ts from contracts/schema
npm run lint
npm run typecheck
npm test               # smoke test + mocks validated against the backend schema
npm run build
npm run dev            # http://localhost:5173
```

Never edit `src/generated/`. Validate mocks with `validateContract()` from `src/contracts.ts`.

## Operator console (CC-04)

The console runs against a contract-valid mock backend until CC-09 wires the live API. Choose a scenario with `?mock=`:
`demo` (T+10, proposal v7), `stale`, `busy`, `loading`, `error`, `empty`, `disconnected`, `degraded`, `world_changing`. Add `&tiles=off` to run without OpenStreetMap tiles.

- `src/api/types.ts` — the `ConsoleApi` seam (CC-09 implements it over HTTP + `/ws/events`).
- `src/mocks/mockApi.ts` — sequences CC-01 fixture payloads; no allocation or policy logic.
- `src/state/` — reducer, plan-view derivation (proposed/stale/approved/dispatched…), labels and reason text.
- `src/components/` — queue, map, triage, fleet, plan panel, approve and override dialogs.

Keyboard: `j`/`k` move through incidents, `Enter` opens triage, `a` focuses Approve (never triggers it), `o` opens the override dialog, `Esc` closes dialogs.

Screenshots: `docs/screenshots/cc-04/` (desktop 1440 px, narrow 390 px).

