# Operations console visual refresh

- Authoring agent: Codex.
- Branch: `codex/console-command-center`, stacked on `claude/cc-11-evaluation` at `11a3af75aeec5094e31bc6c05bcb20a4029d84be`.
- Status: ready for review; not independently approved or merged.
- Authorization: user explicitly requested a futuristic government-style tracking/AI console. This authorizes this frontend presentation task despite the default Claude frontend ownership. Other agents' worktrees were left untouched.

## Delivered

A near-black instrument-panel console derived from the user's supplied visual reference: ivory typography, a single red interface accent, hairline data strips, compact meters, pill navigation and a monochrome map. The centre map is deliberately dominant; both side rails and the telemetry header are narrower, and the mobile map is 72 vh. Metric values and bars are calculated from the server snapshot. Light mode, keyboard controls, simulation labels, severity text, provider attribution and explicit approval states remain visible. No fabricated model confidence, surveillance capability or government affiliation was added.

The presentation stylesheet is separate from existing operational styles. New map styling only touches provider base layers before operational overlays are added. The MapLibre test recorder now implements the newly used `getStyle` API.

## Contracts and behavior

No contract, backend, policy, dispatch or allocation changes. The mission overview displays the actual snapshot event sequence; the KPI component counts snapshot records and derives its meter proportions from those records. The public icon is repository-native SVG. Road-router candidates use neutral ivory so they remain distinct from red proposed routes and white approved routes.

## Verification

- `cd frontend && npm ci` — passed; zero reported vulnerabilities.
- `npm run lint && npm run typecheck && npm test && npm run build` — passed, 52 tests. Existing bundle-size warning remains.
- Browser: Playwright CLI at 1600×1000, 1440×900 and 390×844; inspected desktop, mobile map, selected incident/dock and light-mode screenshots. Keyboard `j` selects incidents; mobile Map tab and theme controls work.
- Live smoke against the newest combined release backend (`6500243`): separate seeded SQLite DB and backend on port 8421; redesigned frontend on 5421. State and WebSocket connected, T+0 advanced, plan v1 approved and simulated dispatch delivered, T+2 advanced, acknowledgement gating worked, and Reset returned the demo to a clean session at sequence 1.
- Screenshots: local ignored `output/playwright/map-expanded.png` and `map-expanded-t0.png`. Live preview: `http://127.0.0.1:5421/` while the documented local processes remain running.
- Revised design: lint, typecheck, all 52 tests and build passed; desktop/mobile screenshots re-inspected after the palette/layout revision.
- Not run: full multi-client browser scenario suite, external model-provider calls, complete manual accessibility audit. Existing automated approval/stale-plan/disconnection tests passed.

## Limitations and handoff

OpenFreeMap's existing `wood-pattern` missing sprite warning may appear; basemap and operational overlays render. The frontend bundle remains large. Full clinical/release validation is outside this visual change.

The concurrent whole-code review at the dependency commit found four backend P1 issues. They remain outside this UI branch; the newest combined release includes their fixes in `4785ee6`, with 211 backend tests, 10/10 adversarial probes and a recorded 17/17 live browser run. The UI smoke test above used that fixed backend.

Next reviewer: review the UI diff and screenshots against the dependency commit, then merge through the existing PR stack. Do not overwrite the active Claude release worktree or mark CC-12 complete based on this visual refresh. If the stack is rebased, cherry-pick this isolated UI commit and rerun frontend checks.
