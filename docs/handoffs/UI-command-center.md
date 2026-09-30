# Operations console visual refresh

- Authoring agent: Codex.
- Branch: `codex/console-command-center`, stacked on `claude/cc-11-evaluation` at `11a3af75aeec5094e31bc6c05bcb20a4029d84be`.
- Status: ready for review; not independently approved or merged.
- Authorization: user explicitly requested a futuristic government-style tracking/AI console. This authorizes this frontend presentation task despite the default Claude frontend ownership. Other agents' worktrees were left untouched.

## Delivered

A warm charcoal operations console with off-white typography, restrained amber accents, rounded situation cards, quieter map colours and a clear operations overview. Decorative panel numbering, glowing frames and the map grid are removed. Metric icons, roomier incident cards, matching favicon and mobile layouts share the same visual language. The triage/reinforcement dock adapts to the available panel width. Light mode, keyboard controls, simulation labels, severity text, provider attribution and explicit approval states remain visible. No fabricated model confidence, surveillance capability or government affiliation was added.

The presentation stylesheet is separate from existing operational styles. New map styling only touches provider base layers before operational overlays are added. The MapLibre test recorder now implements the newly used `getStyle` API.

## Contracts and behavior

No contract, backend, policy, dispatch or allocation changes. The mission overview displays the actual snapshot event sequence; the existing KPI component still counts snapshot records. The public icon is repository-native SVG. The refresh uses muted lavender for road-router candidates; their legend matches.

## Verification

- `cd frontend && npm ci` — passed; zero reported vulnerabilities.
- `npm run lint && npm run typecheck && npm test && npm run build` — passed, 52 tests. Existing bundle-size warning remains.
- Browser: Playwright CLI at 1600×1000, 1440×900 and 390×844; inspected desktop, mobile map, selected incident/dock and light-mode screenshots. Keyboard `j` selects incidents; mobile Map tab and theme controls work.
- Live smoke: separate seeded SQLite DB and backend on port 8317; frontend on 4317 with `CRISIS_BACKEND_URL=http://127.0.0.1:8317`. State and WebSocket connected, scenario controls displayed, T+0 advanced successfully. Existing service on port 8000 was unrelated and returned 404, so it was left alone.
- Screenshots: local ignored `output/playwright/refined-*.png` (current design) and `command-*.png` (earlier interaction checks). Mock preview: `http://127.0.0.1:4317/?mock=demo`; live preview: `http://127.0.0.1:4317/`.
- Revised design: lint, typecheck, all 52 tests and build passed; desktop/mobile screenshots re-inspected after the palette/layout revision.
- Not run: full multi-client browser scenario suite, external model-provider calls, complete manual accessibility audit. Existing automated approval/stale-plan/disconnection tests passed.

## Limitations and handoff

OpenFreeMap's existing `wood-pattern` missing sprite warning may appear; basemap and operational overlays render. The frontend bundle remains large. Full clinical/release validation is outside this visual change.

The concurrent whole-code review at the dependency commit found four additional P1 issues: medical consent crossing session reset, critical confirmed facts not escalating informational incidents, duplicate linking dropping critical needs, and queued delivery not revalidating flood changes. Those backend findings were reproduced and recorded separately; this PR does not resolve them or establish release readiness.

Next reviewer: review the UI diff and screenshots against the dependency commit, then merge through the existing PR stack. Do not overwrite the active Claude release worktree or mark CC-12 complete based on this visual refresh. If the stack is rebased, cherry-pick this isolated UI commit and rerun frontend checks.
