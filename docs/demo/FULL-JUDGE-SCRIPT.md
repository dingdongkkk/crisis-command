# Crisis Command — complete judge demo script

Target length: **8–9 minutes**, followed by questions.

Core line to remember:

> **AI understands and explains. Rules and optimisation allocate. Humans approve risky changes.**

Everything shown is synthetic and every dispatch is simulated. Say that once at the beginning; the interface keeps the same warning visible throughout.

## Before entering the room

1. Start from a clean session:

   ```sh
   scripts/demo.sh --fresh
   ```

   The standard console is `http://127.0.0.1:5321/?tour=show`. During development, use the port printed by the running Vite process; the current UI preview uses `http://127.0.0.1:5421/?tour=show`.

2. Use Chrome, browser zoom 100%, and a window at least 1440×900.
3. Confirm the status says **Live**, simulation time is **T+0:00**, and the scenario has not advanced.
4. Test the microphone once on the presentation laptop and allow permission for this origin. Browser speech recognition may use the browser vendor's recognition service. Crisis Command itself stores no audio.
5. Keep these fallbacks ready:
   - Typed voice-demo phrase: `bhai accident ho gaya, do log ghayal hain, khoon beh raha hai`
   - Offline UI: `http://127.0.0.1:5321/?mock=demo&tour=skip`
   - A second terminal ready to restart `scripts/demo.sh`.
6. Close notifications and unrelated applications.

Do one complete rehearsal with a timer. Reset again before presenting.

## Full presentation

### 0:00–0:45 — Opening and preflight tour

**On screen:** First preflight screen, “A city in motion. One human in command.”

**Say:**

> “Good morning. This is Crisis Command, a simulated emergency decision-support system for Bengaluru. Calls arrive with incomplete information, the available resources are limited, roads can become unreachable, and conditions change while an operator is making a decision.”
>
> “This demonstration uses synthetic data and simulated dispatch only. It has no connection to a real ambulance, police, fire service, patient, or phone network.”

Point to the three statements: **Simulation only**, **Human authority**, and **Live state**.

Click **Continue**.

**Say:**

> “We deliberately separate four responsibilities. Language processing understands caller words. Validated facts retain the evidence and uncertainty. Rules and an optimiser calculate an eligible city-wide plan. A human reviews every risky change before simulated dispatch.”

Click **Continue**.

**Say:**

> “The pressure increases across a ten-minute scenario: cardiac distress, competing incidents, flooding, duplicate reports, a vehicle breakdown and a structural collapse.”

Click **Continue**.

**Say:**

> “During the demo I will advance the scenario, inspect evidence, compare each plan with the previous decision, and approve only what I have actually reviewed.”

Click **Enter command centre**.

### 0:45–1:15 — Orient the judges

**On screen:** Empty live command centre.

Briefly point to the incident rail, large operations map, KPI strip and plan panel.

**Say:**

> “This is a live projection of an append-only event history. The sequence number tells us exactly which world state we are looking at. The left side prioritises incidents, the map shows incidents, units, floods and routes, and the right side explains the current proposal.”
>
> “There are nine synthetic response units: two ALS ambulances, three BLS ambulances, two fire units, one rescue boat and one tow vehicle.”

Do not spend time reading every KPI.

### 1:15–2:30 — T+0: evidence-based triage and human approval

Click **Advance to T+0**. Wait for the badge to return to **Live**.

Select **cardiac chest pain** from the incident queue.

**Say:**

> “At T+0 three reports arrive. One caller reports chest pain and abnormal breathing, identifies themselves as the patient, and asks for a human. The intake keeps each fact with the caller's supporting words. Silence never becomes a reassuring ‘no’; missing critical information remains unknown.”

Point to the triage facts and evidence. Then point to **Non-emergency**.

**Say:**

> “A road-status question and a flat tyre are classified as non-emergencies, so they do not consume an ambulance.”

Point to **PROPOSED vN — not dispatched** in the plan panel.

**Say:**

> “The allocation engine now evaluates all incidents and units together. It considers capability, capacity, road ETA, existing commitments and reserve coverage. This is still only a proposal.”

Tick every required **I understand** checkbox. Click **Approve & dispatch (simulated)**, inspect the confirmation, and confirm.

**Say:**

> “The operator acknowledges the concrete risks and approves this exact plan version. Only now do the routes become approved, and even then the dispatch is simulated.”

### 2:30–3:35 — T+2: competing emergencies and locked units

Click **Advance to T+2**. Select **road accident injuries**, then briefly select **gas leak evacuation**.

**Say:**

> “Two minutes later, a road accident reports heavy bleeding while a gas leak requires evacuation. These incidents compete for scarce resources.”
>
> “Ambulance A1 has reached the cardiac patient and is locked on scene. The replanner cannot pull it away just because a new optimisation would look numerically cheaper. A2, the remaining ALS ambulance, is considered for the accident, while fire capability is considered for the gas leak.”

Point to the plan difference: **New**, **Moved**, **Released** and **Unchanged**.

**Say:**

> “The operator sees the difference from the previously approved plan rather than receiving an unexplained replacement. Every move has a reason and every risky change requires another approval.”

If the flag count is short, acknowledge and approve the T+2 plan. If time is tight, leave it proposed and continue.

### 3:35–4:45 — T+5: flooding, duplicate reports and honest failure

Click **Advance to T+5**. Select both **flood stranded vehicle** reports and leave the duplicate candidate selected.

**Say:**

> “At T+5 two callers appear to describe the same car stranded in floodwater. The system raises a duplicate candidate, but it never merges possible casualties automatically.”

Point to the unmet needs and their explanations.

**Say:**

> “The road router considers one-way roads, closures and flood geometry. Here, no eligible road unit can safely reach the incident. Water navigation is not modelled, so the system says exactly that. It does not draw a straight line, invent an ETA or pretend a road ambulance is a rescue boat.”

Click **Resolve…**, enter a brief reason such as `Same vehicle and caller location`, and choose **Same emergency — link**.

**Say:**

> “A human links the reports. Their provenance remains in the audit history, while duplicate resource demand is removed from the active plan.”

### 4:45–5:45 — T+10: breakdown and resource shortage

Click **Advance to T+10**. Select **structural collapse**.

**Say:**

> “At T+10 a school roof collapses and ambulance A2 breaks down. The world has changed again, and the previously approved assignments cannot be reused blindly.”

Point to **ALS UNMET**, the number of unmet needs and uncovered zones.

**Say:**

> “There are now more critical patients than ALS resources. Crisis Command says ‘No ALS unit is available.’ It may show BLS bridge candidates, but it never relabels BLS as advanced life support. The shortage remains visible and requires human judgement.”
>
> “This is one of the main safety differences from a chatbot: the system can admit that no safe complete answer exists.”

Do not approve every T+10 warning unless the judges ask to see the final confirmation again.

### 5:45–6:50 — Live voice intake

Click **Simulated call**.

**Say:**

> “New reports can also enter during the incident. The operator can type in English, Hindi or Hinglish, or use experimental push-to-talk transcription.”

Choose **English / Hinglish**, click **Start microphone**, and say clearly:

> “Bhai accident ho gaya, do log ghayal hain, khoon beh raha hai.”

Click **Stop**. Pause so the judges can see the transcript.

Correct any transcription mistake in the text box. Select **Koramangala** or another visible synthetic location.

**Say:**

> “Speech never bypasses review. The operator stops the microphone, checks or edits the transcript, selects the reported location, and only then records the synthetic call. Crisis Command stores the text needed for intake, not the audio.”

Click **Record call**. Select the newly created incident.

**Say:**

> “The same evidence and safety pipeline processes the transcript. A new event sequence appears, the report is triaged, and the response plan recalculates against all existing incidents.”

If microphone permission or recognition fails, calmly read the visible error, type the prepared phrase, and continue:

> “The browser recogniser is unavailable, so the typed fallback remains active. The response system does not fail just because an optional provider fails.”

### 6:50–7:35 — Consent-gated synthetic Medical ID

Select the original **cardiac chest pain** incident and open **Medical ID**.

Enter profile reference `mprof_syn_0001` and reason `Check allergies before simulated treatment advice`.

If caller-as-patient confirmation is missing, request access first and show the denial. Then use the incident control to confirm the caller is the patient and request again.

**Say:**

> “Synthetic medical information is separated from the append-only operational log. Access needs active consent, confirmation that the caller is the patient, an active incident and a stated reason. A denial explains the failed condition. Granted values are shown as synthetic and are not copied into the event history.”

Close the dialog.

### 7:35–8:10 — Constrained operator override

Click **Override…**. Attempt to assign or pin a BLS unit to a need that requires ALS, using the available controls.

**Say:**

> “Human control does not mean silently breaking hard safety constraints. An operator can propose a pin, hold, forbid or bridge decision, but an incompatible substitution is rejected with concrete reasons.”

Show the refusal or the constraint explanation.

**Say:**

> “If a BLS bridge is used, it stays labelled as temporary support. The ALS requirement remains unmet.”

### 8:10–9:00 — Evidence and closing

Return attention to the full command centre.

**Say:**

> “Underneath this interface, every command is idempotent, every state change is an event, and replay reconstructs the same state. A stale plan cannot be approved, a retried command cannot dispatch twice, and reconnecting clients receive the events they missed.”
>
> “On 100 seeded synthetic scenarios, compared with a nearest-eligible-unit baseline under the same constraints, the planner reduced the severity-weighted first-decision response from 830 seconds to 757 seconds. It reached 117 critical needs within eight minutes versus 100 for the baseline, and was never worse on that critical-under-eight-minute measure for any seed.”
>
> “Those are synthetic benchmark results, not a clinical or real-city claim.”

Finish with:

> “Crisis Command is not an autonomous dispatcher. It is a controlled decision-support system: AI understands and explains, rules and optimisation allocate, and humans approve risky changes. Its most important feature is not that it always produces an answer. It knows when a safe answer does not exist, explains why, and prevents confidence from becoming an unsafe dispatch.”

Stop. Let the judges ask questions.

## Three-minute version

Use this if the judges reduce the available time.

### 0:00–0:25

Show the first preflight page and say:

> “Crisis Command is a synthetic emergency decision-support simulation. Language processing extracts evidence, deterministic constraints and optimisation calculate a city-wide plan, and a human approves every risky change.”

Skip the guide and enter the console.

### 0:25–1:00

Advance to T+0, select the cardiac incident, show evidence and approve the proposal.

> “The plan is explicitly not dispatched until every risk is acknowledged and a human approves this exact version.”

### 1:00–1:40

Advance directly through T+2, T+5 and T+10, pausing after each returns to **Live**.

> “A unit becomes locked on scene, floods make an incident unreachable, duplicate reports require human resolution, and the last ALS ambulance breaks down. The system recalculates each time without inventing capacity or an ETA.”

Point to **ALS UNMET**.

### 1:40–2:25

Open **Simulated call**, transcribe or type the prepared Hinglish phrase, review it and record the call.

> “Voice only fills an editable transcript. It still enters the same evidence, rules and approval pipeline.”

### 2:25–3:00

Point to the plan diff and close:

> “Every change is replayable and auditable. Against a nearest-unit baseline on 100 synthetic scenarios, this planner improved the severity-weighted first-decision response and reached more critical needs within eight minutes. It is a simulation, not a clinical claim. AI understands and explains; rules and optimisation allocate; humans approve.”

## Judge questions and exact answers

### “What is the AI doing?”

> “The optional language model is limited to extracting structured facts with supporting words and improving explanations. It cannot allocate a unit, create an ETA, approve a plan or dispatch. Deterministic rules and OR-Tools handle allocation, and a human controls simulated dispatch.”

### “Why is this better than finding the nearest ambulance?”

> “Nearest-unit selection handles each call independently. Crisis Command considers all current incidents and resources together, including capability, capacity, commitments, road reachability and reserve coverage. Sending the nearest ALS ambulance to one call may leave a more critical patient with no advanced care.”

### “What happens if the AI is wrong or unavailable?”

> “Every model output is validated against a strict schema and evidence. Invalid, timed-out or unavailable output becomes a visible rules-only degraded state. Unknown critical information remains unknown and escalates; it never silently becomes safe.”

### “Is voice processed locally?”

> “The current voice control uses the browser's experimental speech-recognition API, which may use a browser-vendor service. Crisis Command stores no audio. The operator reviews the resulting text, and typed intake always remains available.”

### “Does Laya run in this version?”

> “No. Laya is an optional future triage-classifier experiment. It would need checkpoint and licence review, language testing, latency measurement and held-out safety evaluation before being enabled.”

### “Can this dispatch a real ambulance?”

> “No. This build intentionally has no route to a real emergency service. Every call, patient, unit and dispatch is synthetic or simulated.”

### “What makes it auditable?”

> “Every state transition is an idempotent append-only event. Plans bind to a planning sequence and version, approvals bind to the plan the operator saw, and replay reconstructs historical state.”

### “What protects medical information?”

> “Medical-profile values live outside the append-only event log. Access requires consent, caller-as-patient confirmation, an active incident and a reason. Revocation clears the stored values, while the audit event contains no medical value.”

### “Is it production-ready?”

> “No. It is a tested decision-support prototype. It lacks production authentication, real service integration, validated clinical triage, real traffic and water navigation. The claims we make are limited to synthetic evaluation.”

### “What did you actually measure?”

> “We measured triage regression behaviour, adversarial safety probes, event replay, browser flows and a 100-seed synthetic allocation benchmark. The benchmark showed a 73.5-second mean improvement in severity-weighted first-decision response, with a bootstrap 95% interval from 54 to 94 seconds.”

## Failure lines during the presentation

Never apologise at length. Read the state, explain the safety behaviour, and continue.

| Problem | Say | Action |
| --- | --- | --- |
| Microphone denied or unavailable | “The optional browser recogniser is unavailable, so the verified text fallback remains active.” | Type the prepared Hinglish phrase. |
| Base map is blank | “Street tiles are unavailable, but operational incidents, routes and constraints remain available.” | Continue using the incident list and overlays. |
| API disconnects | “The console refuses commands on stale state and keeps the last confirmed sequence.” | Use the mock fallback tab or restart the stack. |
| Plan changes during approval | “The world changed, so the system voided an approval for a plan I no longer see.” | Close the dialog and review the new plan. |
| Scenario button is disabled | “The current world change is still being committed and replanned.” | Wait until the status returns to **Live**. |
| Live stack will not recover | “I am switching to the contract-valid offline console; the operational flow is identical.” | Open `?mock=demo&tour=skip`. |

## Claims to avoid

Do not say any of the following:

- “This is connected to Bengaluru emergency services.”
- “The AI dispatches the best ambulance automatically.”
- “These ETAs use live traffic.”
- “The system predicts floods.”
- “The triage is clinically validated.”
- “Voice recognition is fully offline.”
- “Laya powers the current system.”
- “The benchmark proves real-world lives will be saved.”

Use **simulated**, **synthetic**, **decision support**, **proposal**, **measured on the synthetic benchmark**, and **human approval** consistently.
