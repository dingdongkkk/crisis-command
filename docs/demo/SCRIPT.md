# Demo script: Crisis Command (about 8 minutes)

**One line:** AI understands and explains. Rules and optimisation allocate. Humans approve risky changes.

Everything shown is a simulation: synthetic Bengaluru calls, simulated dispatch, no real services. Say this once at the start. The banner on screen says it throughout.

## Before you present (5 minutes)

```sh
scripts/demo.sh --fresh          # console http://127.0.0.1:5321, API :8321
```

- Open the console in a full-screen browser window at 1440×900 or larger. Leave a second tab on `?mock=demo` as the offline fallback (see [FALLBACK.md](FALLBACK.md)).
- Confirm the badge reads **Live · seq 1 · sim T+0:00** and the map shows red-on-black streets.
- Keep [CLAIMS.md](CLAIMS.md) open in case of questions about numbers. Only say what is in the "Measured" column.

## Timeline

| Time | On screen | Say (short) |
| --- | --- | --- |
| 0:00–0:40 | The empty console | "A city control room during a flood night. Calls arrive in English, Hindi and Hinglish. Nine synthetic units: 2 ALS ambulances, 3 BLS, 2 fire, a boat, a tow truck. The system never dispatches on its own: every change is a proposal a human approves." |
| 0:40–1:40 | **Advance to T+0** | "Three calls. The first: *chest pain, not breathing normally, I am the patient, I want a human*. The rules read each fact with the exact words as evidence, and flag it critical. A road question and a flat tyre are **not** emergencies, so they go to *Non-emergency* and use no ambulance." Click the cardiac incident: facts, evidence spans, *With operator — caller requested human*. |
| 1:40–2:40 | Plan panel: **PROPOSED v1 — not dispatched** | "The optimiser proposes a plan: nearest *eligible* units, hospital capacity, and reserve coverage for the rest of the city. It is labelled *not dispatched*. Approval needs every flag acknowledged, each saying what it is about." Tick the boxes, then **Approve & dispatch (simulated)**. The routes turn solid white: **DISPATCHED (simulated)**. |
| 2:40–3:40 | **Advance to T+2** → approve v2 | "A road accident with heavy bleeding, and a gas leak evacuating 20 people. A1 reached the cardiac patient and is now **locked** on scene: the plan never pulls a unit off a patient. A2, the second and last ALS ambulance, goes to the accident." Point at the plan diff: added, moved, unchanged. |
| 3:40–4:40 | **Advance to T+5**; select the second flood report | "Two callers describe the same car stranded inside the flood. The plan flags a *possible duplicate* that must be acknowledged; it never merges on its own." Under **Unmet needs**: "*No eligible unit can reach it by road*, and *water access is not modelled*. The system says what it cannot do instead of inventing an ETA." Then **Resolve… → Same emergency — link**: "Its demand merges into the first report, so nothing the second caller said is lost." |
| 4:40–5:40 | **Advance to T+10**; open the approve dialog | "A school roof collapses, and ambulance A2 breaks down. Now there are more critical patients than ALS ambulances. The plan says *No ALS unit is available*, and the red strip at the bottom says how many critical needs are unmet." While the approve dialog is open, a world change voids it: **Plan changed — nothing approved**. "An approval is bound to the exact plan version; your click cannot approve something you did not see." (To force this live, break down a unit through the API during the dialog, or show `docs/screenshots/cc-12-p1/02-plan-changed-dialog.png`.) |
| 5:40–6:30 | Cardiac incident → **Medical ID** | "Medical records only with consent, only if the caller is the patient, only for an active incident, and only with a reason." Request: denied, *not confirmed that the caller is the patient*. Confirm yes, then request again: the values are shown once, labelled SYNTHETIC, and never written to the log. |
| 6:30–7:15 | **Override…** → pin BLS unit B2 to an ALS need | Refused: *B2 is not an eligible type… use a BLS bridge*. "Operators can override, but not into an unsafe plan, and they are told exactly why." Optionally approve a BLS bridge instead. |
| 7:15–8:00 | Resilience | "If the network drops, the console says *Disconnected*, keeps the last data, and disables approval; on reconnect it replays exactly what it missed. If the AI model fails, intake falls back to rules and says so." (Model drill screenshot: `docs/screenshots/cc-10/model-drill/06-model-degraded.png`.) Close with the measured result from CLAIMS.md: "Against a nearest-unit baseline on 100 seeded scenarios, faster severity-weighted response, and more critical calls under 8 minutes, never worse. Synthetic, and not a clinical claim." |

## If asked

- **Is this real dispatch?** No. There is no route to any real service, and dispatch is simulated by design.
- **Is the AI deciding?** No. The language model (optional) only extracts facts with evidence. Allocation is an auditable optimiser, and approval is always human.
- **How do you know it works?** 211 backend tests, a replay check on every event, 10 adversarial probes, a 100-seed benchmark and a scripted browser run. See CLAIMS.md.
- **What doesn't it do?** Water navigation, real traffic, authentication, clinical triage. See the limitations in CLAIMS.md.
