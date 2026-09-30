# UI: data-strip theme (on top of Codex's command-centre refresh)

- Author: Claude (claude-opus-5-5). The user asked for the look of a supplied reference and for the work to build on Codex's `codex/console-command-center` (#29).
- Branch and PR: `claude/ui-data-strip` (#31) = #29 + a merge of `claude/cc-12-release` (#30) + this theme. It is presentation-only: no backend or contract changes.

## What changed

**`frontend/src/data-strip.css`** (loaded after Codex's `command-center.css`):

- Black panels with hairline rules, and uppercase IBM Plex Mono labels.
- Large thin numerals for the key figures.
- Controls:
  - a white pill for the active or primary control;
  - pill tabs;
  - on phones, a bottom pill navigation bar.
- Red is reserved for:
  - the city tag;
  - alerts;
  - critical state;
  - the selected incident.

**Header** (`CommandHeader.tsx`):

- The `BLR_01` tag.
- The live active-emergency count as the hero figure.
- A `[ STATUS: … ]` chip, derived from the plan: `CRITICAL_DEMAND_UNMET`, `CRITICAL_RESPONDING`, `RESPONDING` or `CLEAR`.
- A readout of sim time, event sequence, session and dispatch mode. The session ID is shown verbatim.

**Stat strip** (`KpiStrip.tsx`): `UPPER_SNAKE` labels, plus segmented bars for the share of the fleet that is free and the share of demand that is met.

**Alert strip** (`CommandFooter`): red when critical demand is unmet in the current plan. For example:

```
ALERT: 4_CRITICAL_NEEDS_UNMET · SOME_UNREACHABLE_BY_ROAD — REVIEW PLAN
```

It is neutral otherwise, and every value comes from server state.

**Map:** the base map is re-tinted to near-black land with red roads and water. Operational overlays keep their meanings:

- approved routes are solid white;
- proposed routes are dashed amber;
- floods are blue.

## Kept deliberately

- All state words are still text: `PROPOSED … not dispatched`, `DISPATCHED (simulated)`, severity labels and flags.
- Dialog titles and plan sentences keep normal case, for readability. The live end-to-end test reads them exactly.
- IDs are never re-cased.

## Verification

- `npm run lint`, `npm run typecheck`: clean.
- `npm test`: 53 passed.
- `npm run build`: built.
- Live console end-to-end run: **17/17** (`docs/screenshots/ui-data-strip/`).
- Checked by hand at 1440×900 and 375×812. There is no horizontal overflow on the phone.
