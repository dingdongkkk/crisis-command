# 0006 — Operator console and intake screen states

Status: accepted (CC-01), revised after Codex review — see [0009](0009-review-resolutions.md). Consumers: CC-04 (mocks), CC-06 (intake), CC-09 (live wiring).

## Layout (desktop ≥ 1280 px)

```
┌ Connection/mode banner ─────────────────────────────────────────────┐
│ Incident queue │            Map                  │ Plan panel      │
│ (sorted)       │ incidents, units, flood, zones  │ diff, flags,    │
│                │                                 │ approve/override│
├────────────────┴──────────────┬──────────────────┴─────────────────┤
│ Triage / intake for selected  │ Fleet list        │ Event timeline │
└───────────────────────────────┴───────────────────┴────────────────┘
```

Narrow (< 900 px): tabs `Queue · Map · Plan · Triage · Fleet`; the banner and a sticky plan-status bar stay visible on every tab. The Approve control is only on the Plan tab.

## Global rules

- Status is always text + icon + colour; never colour alone. Severity badges read `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
- The word **"simulated"** appears on every dispatch-related label: "Approve & dispatch (simulated)", "Dispatched (simulated)".
- Selected incident, open panel and scroll position persist across live updates and resyncs.
- All actions are keyboard reachable in visual order; `j/k` move through the queue, `Enter` opens, `a` focuses Approve (does not trigger it), `o` opens override, `Esc` closes dialogs. Dialogs trap focus and return it on close.
- Unknown enum values render as "Unrecognised (<value>)" and disable Approve.

## Connection banner

| State | Trigger | Shows | Commands |
| --- | --- | --- | --- |
| `connecting` | initial load | skeletons, "Connecting…" | disabled |
| `live` | hello + subscribed | "Live · seq 61 · sim T+10:00" | enabled |
| `resyncing` | sequence gap / new session / backlog not yet caught up | "Resyncing from server…" last good data dimmed | disabled until server confirms catch-up |
| `disconnected` | 30 s silence / socket closed | "Disconnected — data as of seq 61, 00:42 ago. Retrying in 4 s" + Retry | disabled |
| `degraded` | `ModelAdapterDegraded`, routing fixture fallback, solver fallback | "Degraded: language model unavailable — rule intake active" (one line per cause) | enabled |
| `world_changing` | material events arriving faster than a proposal can be reviewed | "World changing — plan v8 recomputing" + Pause scenario | Approve disabled; Pause enabled |
| `replay` | operator enters replay | "REPLAY · read-only · seq 42 of 118" | disabled except replay controls |
| `error` | snapshot fetch fails | problem `title` + `code`, Retry | disabled |

Commands are disabled while not `live`/`degraded` because the operator cannot know the current planning sequence.

## Intake panel (per report / incident)

| State | Shows | Controls |
| --- | --- | --- |
| `empty` | "Select an incident or start a simulated call" | New simulated call |
| `receiving` | caller text transcript (synthetic) | Send, "Caller asks for a person" |
| `extracting` | spinner "Extracting facts (rules)" / "(rules + model)" | none new |
| `question` | one targeted question, Yes / No / Not sure buttons, question count "1 of 2" | answer, skip to operator |
| `facts` | fact table: key, value (`YES`, `NO`, `UNKNOWN`), source, evidence highlight, `PROVISIONAL`/`CONFLICT` tags | Confirm fact (operator) |
| `escalated` | "With operator — reason: Life threat indicated" persistent strip | operator answers; cannot un-escalate |
| `model_unavailable` | "Model unavailable — rule-based facts only; unknowns kept" | continue |
| `non_emergency` | "No emergency unit needed · Information request" with category | Upgrade category (records reason) |

Critical `unknown` facts are listed first with "Not established — treated as present for planning".

## Plan panel

| State | Shows | Approve | Override |
| --- | --- | --- | --- |
| `no_plan` | "No proposal. Approved plan v6 in force." | hidden | enabled |
| `computing` | "Computing plan after seq 61…" + previous approved plan | disabled | disabled |
| `proposed` | "PROPOSED v7 — not dispatched" header, diff, flags, solver status | enabled when all `requires_ack` flags ticked | enabled |
| `stale` | "STALE — world changed at seq 61 (A2 broke down). Recomputing." diff greyed | disabled | disabled |
| `approving` | "Approving v7…" | disabled (spinner) | disabled |
| `approved` | "APPROVED v7 — dispatch queued (simulated)" | hidden | enabled |
| `dispatched` | "DISPATCHED (simulated) v7" per assignment ✓ | hidden | enabled |
| `dispatch_partial_failed` | per-command ✓ sent / ✕ failed / ⊘ cancelled (e.g. unit broke down before delivery) with reason | hidden | enabled; "Recompute" |
| `failed` | "No valid plan could be computed. Approved plan v6 remains in force." + reason codes | hidden | enabled |
| `approval_rejected` | toast + inline: "Not approved: plan changed (now v8). Review the new plan." | returns to `proposed` v8 | — |
| `revalidated` | "Approved plan v7 still current (checked at seq 72)" | hidden | enabled |
| `session_changed` | "Simulation was reset. Your action was not applied." (`STALE_SESSION`) then full resync | disabled | disabled |
| `database_busy` | "Server busy — retrying" (`DATABASE_BUSY`); the client retries the **same** idempotency key after `Retry-After` | disabled (spinner) | disabled |

### Diff presentation

Grouped: **Changed** (unit moved: `B3: zone_north reserve → inc_0006 school collapse`, ETA old→new), **New**, **Released**, **Unchanged** (collapsed), **Unmet** (always expanded when present). Each row has "Why" (reason facts) and each unmet row has "Why not" listing each candidate unit and its blocking reason code. Totals: weighted ETA delta, units moved, needs unmet, zones uncovered.

### Flags

Each flag row: severity text, message, `requires_ack` checkbox labelled with the consequence ("I understand inc_0006 has no ALS unit"). `ALS_UNMET` rows show BLS bridge candidates with "Propose BLS bridge…" which opens the override dialog pre-filled. The Approve button's accessible name includes the count of unacknowledged flags.

## Approval dialog

Summary of changes and flags → "Approve & dispatch (simulated)" / Cancel. Sent with `expected_session_id`, `expected_plan_version`, `expected_planning_sequence`, `acknowledged_flag_ids`. On `STALE_PLAN` the dialog closes, the panel switches to the new version and focus moves to its header. The client never retries an approval automatically against a different version.

## Override dialog

| State | Shows |
| --- | --- |
| `editing` | kind selector, unit/need pickers limited to structurally compatible choices, reason text (required) |
| `submitting` | spinner |
| `rejected` | each conflict: code in words ("A1 is on scene at inc_0001 and locked"); nothing applied |
| `accepted` | "Override recorded. Recomputing plan…"; dialog closes when proposal arrives, soft consequences shown on the plan |
| `stale` | "World changed before your override was recorded. Review and retry." |

Active overrides list with Revoke; rejected and invalidated overrides remain visible in history with reason.

## Replay mode

- Entered from the timeline; exit returns to `live` and resyncs.
- Scrubber by sequence with step ±1, jump to event types (plan proposed/approved, unit breakdown, flood update).
- Shows the map, queue, plan and facts as of the selected sequence, from server state at that sequence.
- All command controls are removed (not just disabled); a persistent "REPLAY · read-only" banner. Replay never triggers dispatch, solver or models.

## Map

Incidents (shape by category + severity text label), units (type glyph + ID + status; raw observed position shown distinct from the planning-tick position used for ETAs), flood polygons with version label, reserve zones (outline; hatched when uncovered), route polylines for proposed (dashed) vs approved (solid). Required OpenStreetMap/tile attribution always visible. If tiles fail, a plain-coordinate fallback canvas still shows features and "Map tiles unavailable".
