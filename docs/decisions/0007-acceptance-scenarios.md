# 0007 — Demo fixture and acceptance scenarios

Status: accepted (CC-01). All data is synthetic. Place coordinates are approximate public locations used only to put fictional incidents on a Bengaluru map. Assertions are about invariants, flags and states; exact ETAs and which specific BLS unit is chosen come from the computed plan, not from this document.

## Fixture `demo-bengaluru-v1`

Units (`[lon, lat]` = station):

| ID | Type | Home zone | Station | Extra |
| --- | --- | --- | --- | --- |
| `unit_A1` | als | `zone_central` | `[77.6070, 12.9750]` | |
| `unit_A2` | als | `zone_south` | `[77.6245, 12.9352]` | |
| `unit_B1` | bls | `zone_central` | `[77.5946, 12.9716]` | |
| `unit_B2` | bls | `zone_south` | `[77.5838, 12.9250]` | |
| `unit_B3` | bls | `zone_north` | `[77.5920, 13.0358]` | |
| `unit_F1` | fire | `zone_central` | `[77.6010, 12.9780]` | |
| `unit_F2` | fire | `zone_east` | `[77.7000, 12.9600]` | |
| `unit_BT1` | boat | `zone_east` | `[77.6784, 12.9400]` | `capacity_persons: 6` |
| `unit_T1` | tow | `zone_east` | `[77.6600, 12.9500]` | |

Facilities: `hosp_H1` `[77.5960, 12.9580]` capabilities `emergency, cardiac`, `ed_beds_available: 4`; `hosp_H2` `[77.6480, 12.9160]` `emergency`, `ed_beds_available: 6`; `shelter_S1` `[77.6100, 12.9500]` `capacity_persons: 120, occupied_persons: 30`; `shelter_S2` `[77.6400, 12.9900]` `capacity_persons: 80, occupied_persons: 0`.

Reserve zones (`coverage_eta_s: 600`): `zone_north`, `zone_central` and `zone_south` each require one `bls` (satisfied by `bls` or `als`); `zone_east` has no ambulance requirement in v1 (no ambulance is stationed there, so a requirement would be permanently uncovered and meaningless). CC-03 authors the polygons; each zone's reference point is its station above.

Routing: CC-07 records a road fixture covering these points; the flood polygon `flood_bellandur` closes roads around `[77.6784, 12.9304]` from T+5.

## Timeline

| sim time | Event(s) | Expected |
| --- | --- | --- |
| T+0 (0 s) | `rpt_0001` Indiranagar `[77.6408, 12.9784]`: caller, 58, chest pain, synthetic history | `inc_0001` critical, ALS need; `EscalatedToHuman(LIFE_THREAT_INDICATED)`; A1 proposed |
| T+0 | `rpt_0002` "Is Outer Ring Road open?" | `information_request`, no needs |
| T+0 | `rpt_0003` tyre puncture, Bellandur `[77.6784, 12.9304]`, vehicle driveable | `inc_0003` `non_emergency_assist`, no needs, no tow assigned |
| T+2 (120 s) | `rpt_0004` road accident, Silk Board `[77.6229, 12.9177]`, 2 injured, `conscious: unknown` | `inc_0004` high, ALS (provisional) + BLS |
| T+2 | `rpt_0005` gas leak, HSR `[77.6387, 12.9116]`, 40 residents | `inc_0005` high, fire + 40 shelter places |
| T+5 (300 s) | `FloodZoneUpdated flood_bellandur v1`; `rpt_0007` from inc_0003 caller: water rising, 2 people in car | `inc_0003` upgraded to emergency, `water_rescue` need (boat); road units cannot reach |
| T+5 | `rpt_0008` passer-by reports car in water near Bellandur | `DuplicateCandidateFlagged` rpt_0008 ↔ inc_0003; not merged automatically |
| T+10 (600 s) | A1 `on_scene` at inc_0001; `unit_A2` `broken_down` while en route to inc_0004 | A2's assignment invalidated |
| T+10 | `rpt_0010` school roof collapse, Jayanagar `[77.5838, 12.9300]`, children trapped, count unknown | `inc_0006` critical: ALS + 2 BLS + fire |

At T+10 there are two ALS needs (inc_0004, inc_0006) and no eligible ALS (A1 locked, A2 broken down).

## Acceptance scenarios

Each is a CC-11 / CC-09 test case. "Plan" means the newest proposal unless stated.

### Intake and triage

- **AS-01 Unknown stays unknown.** Given `rpt_0004` text with no mention of consciousness, when facts are extracted by rules only, then `conscious` is `unknown`, the ALS need has `basis: provisional_unknown`, the triage panel lists it under "Not established", and no fact is `no`.
- **AS-02 Negative needs evidence.** Given a model adapter returning `breathing_normally: no` with no evidence span, then the stored value is `unknown` with reason `NEGATIVE_WITHOUT_EVIDENCE`.
- **AS-03 Model timeout.** Given the model adapter times out on `rpt_0001`, then rule facts still produce `inc_0001` critical with ALS need, `EscalatedToHuman` is emitted, and the banner shows `degraded` with the model cause.
- **AS-04 Human request.** Given the caller presses "Caller asks for a person" or types "kisi insaan se baat karao", then `EscalatedToHuman(CALLER_REQUESTED_HUMAN)` is emitted regardless of model state.
- **AS-05 Non-emergency does not consume units.** Given `rpt_0002` and `rpt_0003` at T+0, then no plan assigns any unit to them and they appear in the non-emergency queue.
- **AS-06 Upgrade.** Given the T+5 flood and `water_rising: yes` on inc_0003, then `IncidentCategoryChanged` to `emergency` with reason `CATEGORY_UPGRADED`, and the next plan assigns `unit_BT1` or lists the water-rescue need as unmet with reasons; no road unit is assigned across the closed polygon.
- **AS-07 Duplicate candidate.** Given `rpt_0008`, then a `DuplicateCandidateFlagged` appears for operator review, inc_0003 and rpt_0008 both remain, and people counts are not summed or merged automatically.

### Allocation and plan diff

- **AS-10 Invariants.** For every plan in the scenario: no unit has two tasks; every assigned unit is of eligible type, not unavailable, and has `route_status: ok`; shelter persons ≤ free capacity; locked units keep their task.
- **AS-11 Locked unit.** At T+10, A1 is `on_scene`; the plan keeps A1 on inc_0001 and inc_0006's "Why not A1" shows `UNIT_LOCKED on_scene`.
- **AS-12 Breakdown invalidates.** When A2 becomes `broken_down`, its assignment to inc_0004 is removed in the next plan and the diff shows it under Changed/Released with reason `UNIT_UNAVAILABLE`.
- **AS-13 ALS shortage explicit.** At T+10 the plan has ALS unmet needs for inc_0004 and inc_0006, each with `ALS_UNMET` (`critical`, `requires_ack`), `bridge_candidates`, and no BLS unit labelled or counted as ALS.
- **AS-14 Reserve soft.** If the T+10 plan moves the last ambulance out of a reserve zone's coverage, the plan has `RESERVE_UNCOVERED` for that zone and **does not** leave any need unmet to keep it covered.
- **AS-15 Minimal diff.** The T+10 plan changes no assignment that is unaffected by the breakdown/new incident unless it reduces the objective beyond the reassignment penalty; each changed row shows old→new unit and ETA and a Why.

### Approval and staleness

- **AS-20 Ack required.** Approving the T+10 plan without acknowledging every `requires_ack` flag returns `409 UNACKNOWLEDGED_FLAGS`; the plan remains `proposed`.
- **AS-21 Stale approval.** Given plan v7 based on planning sequence 58, when `UnitStatusChanged` (seq 59) commits before the approval, then the approval returns `409 STALE_PLAN` with the current proposal, `ApprovalRejected` is logged, and no `SimulatedDispatchQueued` exists for v7.
- **AS-22 Double approval.** Two concurrent approvals of v7 with different idempotency keys: exactly one `PlanApproved`; the other gets `PLAN_NOT_PROPOSED`.
- **AS-23 Idempotent retry.** Retrying the approval with the same key and body returns the original 200 body with `Idempotent-Replayed: true`; one `PlanApproved`, one set of outbox entries.
- **AS-24 Proposed is not dispatched.** Before approval, every UI surface labels v7 `PROPOSED — not dispatched`; unit markers keep their approved-plan state.

### Overrides

- **AS-30 Conflicting pin.** Pinning `unit_A1` to inc_0006 at T+10 returns `409 OVERRIDE_CONFLICT` with `UNIT_LOCKED`; `OverrideRejected` is recorded; the plan is unchanged.
- **AS-31 BLS bridge.** Operator approves a BLS bridge from inc_0006's bridge candidates; the new plan shows the BLS unit with `role: bridge`, flag `ALS_UNMET_BLS_BRIDGING` still `critical`, and ALS unmet cost unchanged.
- **AS-32 Invalidated override.** A pin on `unit_B2` followed by B2 `out_of_service` yields `OverrideInvalidated` and flag `OVERRIDE_INVALIDATED` on the next plan.
- **AS-33 Override consequences.** An accepted `hold_unit` on `unit_B3` shows `soft_consequences` (weighted ETA delta, any newly unmet need with `OVERRIDE_CAUSES_UNMET`).

### Replay and connection

- **AS-40 Replay equivalence.** After the full scenario, replaying all events into an empty store gives the same projection hash; no additional `SimulatedDispatchSent` is appended.
- **AS-41 Replay is read-only.** In replay mode no command control is present; keyboard shortcuts for approve/override do nothing.
- **AS-42 Gap recovery.** If the client receives seq 63 after 61, it stops applying, fetches `/state`, resubscribes, and ends with the same state as a fresh load; the selected incident remains selected.
- **AS-43 Disconnect.** After 30 s without messages the banner shows `disconnected` with last sequence and age, and Approve/Override are disabled.
- **AS-44 Reset.** `POST /demo/reset` creates a new `session_id`; connected clients discard state and resync to sequence 1.

### Medical ID

- **AS-50 Consent gate.** A profile read for inc_0001 succeeds only when the synthetic profile has consent, `caller_is_patient: yes`, inc_0001 is active and the operator gives a reason; otherwise `403 PROFILE_ACCESS_DENIED` with the failing reason; both cases append an access event without profile values.
