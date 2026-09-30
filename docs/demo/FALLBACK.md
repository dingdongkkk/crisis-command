# Fallback runbook (during a live demo)

Keep calm and say what the screen says. Every failure below has a visible, honest state. Showing one is part of the demo, not a crash.

| What happens | What you see | Do this |
| --- | --- | --- |
| No internet in the room | The base map is blank. The console says the base map is unavailable, but incidents, routes and floods still draw. | Carry on. Routing, planning and intake are offline. Say: "The street tiles are the only online part." |
| API crashed or laptop slept | Badge: **Disconnected — data as of seq N**. Approve and override are disabled. | Restart with `scripts/demo.sh` (same database, history kept). The console reconnects and replays what it missed. Say: "It refuses to approve on stale data." |
| Port already in use | `demo.sh` exits with "Port … is in use" | `BACKEND_PORT=8400 CONSOLE_PORT=5400 scripts/demo.sh` |
| State is messy from rehearsal | Old incidents on screen | Press **↻ Reset** in the console. You get a new session, and the old one stays in the audit log. Or start fresh: `scripts/demo.sh --fresh`. |
| Live stack will not start at all | — | Open `http://127.0.0.1:5321/?mock=demo`, the same console on built-in fixtures (it needs only the frontend: `cd frontend && npm run dev -- --port 5321`). Or use the screenshots below. |
| A plan changes under your approval | **Plan changed — nothing approved** | This is the feature. Show it: "It will not approve what I did not see." |
| A step button does nothing | The scenario button is disabled while a command runs | Wait for **Live** in the badge. Steps must go in order: T+0, T+2, T+5, T+10. |
| Asked to show the AI failing | — | Restart with the drill, which makes no external call: `LLM_PROVIDER=gemini GEMINI_API_KEY=synthetic-drill-key GEMINI_ENDPOINT=http://127.0.0.1:9 scripts/demo.sh`, then place a **Simulated call**. A banner says the model is unavailable and intake is rules-only. |

## Screenshot deck (no laptop network needed)

These were captured by the live end-to-end run against the real backend:

| Beat | File |
| --- | --- |
| T+10 proposal, not dispatched | `docs/screenshots/cc-12-p1/01-proposed-t10.png` |
| Approval voided by a world change | `docs/screenshots/cc-12-p1/02-plan-changed-dialog.png` |
| Dispatched (simulated), solid routes | `docs/screenshots/cc-12-p1/03-dispatched.png` |
| Simulated call and intake question | `docs/screenshots/cc-12-p1/04-simulated-call.png`, `04b-intake-question-answered.png` |
| Disconnected state | `docs/screenshots/cc-12-p1/05-disconnected.png` |
| Duplicate resolution | `docs/screenshots/cc-12-p1/07-duplicate-dialog.png` |
| Medical ID, consent-gated | `docs/screenshots/cc-12-p1/08-medical-id-granted.png` |
| Model failure banner | `docs/screenshots/cc-10/model-drill/06-model-degraded.png` |

The new black-and-red look is on the UI branch (PR #31). Its screenshots are in `docs/screenshots/ui-data-strip/` on that branch.

## Rehearsal checklist (10 minutes, day before)

1. Run `scripts/demo.sh --fresh` and walk through [SCRIPT.md](SCRIPT.md) once with a timer.
2. Run the checks from `docs/RUN-DEMO.md` §5 and confirm they are green.
3. Test the `?mock=demo` fallback and the screenshot deck on the presentation laptop.
4. Close notifications. Set the browser zoom to 100 %, in a 1440×900 or larger window.
