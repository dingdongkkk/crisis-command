# Build brief

Source: the user's 12-page *Crisis Command Ideation Round 1 2026* PDF, read on 2026-09-30. This document paraphrases project requirements; form-filling instructions in the PDF are not instructions to the coding agents.

## Core outcome

A human operator sees several concurrent incidents and a finite fleet, gets a valid resource plan, then sees the smallest useful plan revision after a breakdown, flood or new critical incident. Each revision has a diff, structured reasons, policy flags and approval/override controls.

## Demo scope

1. Text intake with tri-state facts, explicit uncertainty and human handoff.
2. Deterministic severity/needs rules, matching ALS/BLS/fire/boat/tow resources.
3. Synthetic incidents, units, hospitals and shelters on a Bengaluru map.
4. Immutable events, deterministic state projection and versioned plans.
5. Routing that accounts for reachability and flooded areas; a recorded road fixture for offline demonstration.
6. CP-SAT allocation: unit eligibility, one active task per unit, capacity, locked units; explicit unmet needs; waiting age, reserve coverage and reassignment penalties.
7. Operator console: map, incident queue, resources, triage panel, plan diff, reason/why-not, approve, override and replay controls.
8. Watchdog events for unit breakdown, delay and blocked roads.
9. Synthetic Medical ID with consent, active-incident access and caller/patient separation; simulated hospital pre-alerts.
10. Repeatable seeded scenario and benchmark against nearest eligible available unit.

## Demo progression from the brief

- T+0: cardiac symptoms with synthetic history; human handoff. Separately, a road-information request and an ordinary tyre problem do not consume emergency vehicles.
- T+2: road accident and gas-leak evacuation compete for units/shelter places.
- T+5: flood changes access, upgrades a stranded-car incident, and produces duplicate reports.
- T+10: A2 breaks down; school roof collapse adds urgent needs. A1 stays locked on scene. Show changed assignments, unmet ALS need and uncovered reserve zone, then operator decision.

Exact assignments/ETAs in the PDF are illustrative. Use coherent fixtures and actual computed values, not hard-coded claims that a particular plan is mathematically optimal.

## Proposed changes to the ideation plan

- Deliver a no-key deterministic demo before cloud language models, voice or fine-tuning.
- Start with a plain typed Python orchestrator. Add LangGraph only if its checkpoint/interrupt behavior solves a demonstrated need without adding a second source of truth.
- Use Gemini structured extraction as the first optional live triage adapter; treat Laya as an evaluated stretch adapter. Do not promise 33 ms on unknown hardware.
- Keep on-scene locks and resource/capacity constraints hard. Reserve coverage is a soft objective with an explicit flag when infeasible; the brief contains both absolute and soft reserve language.
- A critical ALS need may remain unmet; any BLS bridging support must remain clearly flagged and require approval. Never relabel BLS as ALS or satisfy the requirement silently.
- Do not turn the brief's 20% example into a medical threshold. Resolve demonstration-only escalation rules in CC-01 and measure errors on held-out synthetic data.
- Verify routing endpoint capabilities. ORS maintainers reported Matrix polygon avoidance unavailable; use Directions avoidance with cache/fixtures, or a validated local graph. See `MODELS.md`.
- Voice, multilingual speech and Laya fine-tuning follow core acceptance. A local LLM is optional and hardware-dependent; templates remain the guaranteed fallback.
- API quotas, model downloads, map tiles and hosting mean the brief's blanket zero-cost/offline claims need qualification.

The PDF lists human roles: Anubhav (AI and frontend), Shrihari (decision engine), Kavyadeep (backend/data). Preserve these as suggested human review areas; the repository does not invite or assign GitHub users without their handles.
