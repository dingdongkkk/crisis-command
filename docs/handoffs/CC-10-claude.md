# CC-10: Duplicate resolution, Medical ID contract and console controls

- Authoring agent/model: Claude (claude-opus-5-5). This completes the "wire required UI controls" part of CC-10, on top of the Codex backend (`docs/handoffs/CC-10.md`, #24).
- Branch and PR: `claude/cc-10-completion`, stacked on `claude/cc-09-live` (#26). PR body carries `Closes #10`.
- Dependency commits/PRs consumed: CC-09 `6a16a00`, and the Codex CC-10 backend through #25.
- Reviewer agent/model and reviewed commit: Codex/Astra — pending
- Status: ready for review

## Delivered

**Duplicate reports** (review finding #23-1: double-counted demand with no way to resolve it):

- Plans flag every active duplicate candidate with `DUPLICATE_CANDIDATE_UNRESOLVED` (warning, acknowledgement required). The double counting is visible and must be acknowledged before approval. Nothing merges automatically (0007 AS-07).
- `POST /incidents/{id}/duplicates/{report_id}/resolve` (0008). `{id}` is the original incident, and `report_id` is the report whose incident was flagged. Both outcomes append `ReportLinkedToIncident` (planning-affecting) and trigger replanning.
  - `linked`: the report joins the original, and the candidate becomes `merged_duplicate`, so its needs leave planning.
  - `kept_separate`: both stay active and the candidate marker is cleared.
- A pair that is not a candidate returns `409 NOT_A_DUPLICATE_CANDIDATE` with the current candidates.
- Console: the triage panel shows "Possible duplicate of …" with a **Resolve…** dialog (reason required, link or keep separate).

**Medical ID now follows 0008 / AS-50** (review finding #24; the earlier contract drift):

- The path is `POST /incidents/{id}/medical-profile-access`, using the contract `MedicalProfileAccessCommand`. The old `/medical-profile/access` path is removed.
- `caller_is_patient` is a triage fact, recorded by the operator through the existing `POST /incidents/{id}/facts/caller_is_patient/confirm`. It is operator-only: intake never asks it and allocation never reads it. A missing or unknown value denies access.
- Denials return `403 PROFILE_ACCESS_DENIED` with `reason`, checked in this order:
  1. `MISSING_OPERATOR_REASON`
  2. `INCIDENT_NOT_ACTIVE`
  3. `PROFILE_NOT_LINKED` (profiles carry `linked_incident_id`)
  4. `NO_CONSENT` / `CONSENT_REVOKED`
  5. `CALLER_IS_PATIENT_UNKNOWN`
  6. `CALLER_IS_NOT_PATIENT`
- Every attempt appends `MedicalProfileAccessGranted` or `MedicalProfileAccessDenied`, carrying the reason and field names only.
- The value read rechecks every rule under the writer lock, so a replayed receipt after revocation returns `CONSENT_REVOKED`.
- The demo seeds synthetic profile `mprof_syn_0001` for the T+0 cardiac caller ("I am the patient"). The values are invented and labelled SYNTHETIC.
- Console: a **Medical ID (consent-gated)…** dialog.
  - Confirm caller-is-patient yes or no.
  - Enter the reference and a reason.
  - A denial reason is explained in plain text.
  - Granted values are shown once inside the dialog and never stored in client state after it closes.

**Also fixed:**

- Answering an intake question no longer drops facts an operator had confirmed. Operator confirmations are fed into the session and carried over (regression test included).
- `POST /plans/recompute` returns `202` (0008).

## Contract or data changes

- `contracts/openapi.json`:
  - adds the resolve endpoint;
  - renames the medical access path;
  - recompute now returns `202`.
- The JSON Schema is unchanged. The existing `DuplicateResolveCommand`, `MedicalProfileAccessCommand` and `merged_duplicate` status are used as-is.
- `ReportLinkedToIncident` projection semantics: `kept_separate` now clears the candidate marker, and `linked` marks an emptied candidate `merged_duplicate`. The fold stays deterministic, and replay equality is tested.
- Private `profiles` rows gain `linked_incident_id` and `consent_revoked`.

## Verification

| Command | Outcome |
| --- | --- |
| `python3 scripts/validate_setup.py`, `python3 -m unittest discover -s tests` | passed |
| `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy` | passed (66 source files) |
| `cd backend && uv run pytest` | 195 passed |
| `cd backend && uv run python -m app.contracts.export --check` | passed |
| `cd frontend && npm run gen:contracts && git diff --exit-code -- src/generated` | no drift |
| `cd frontend && npm run lint && npm run typecheck && npm test && npm run build` | passed, 52 tests |

New backend tests (`tests/test_medical_and_duplicates.py`):

- every denial reason, checked in rule order;
- no values in the log or receipts;
- the old path is gone;
- the demo profile;
- the operator fact survives answers;
- the duplicate flag;
- link and keep-separate outcomes;
- replay equality.

Frontend: `IncidentDialogs.test.tsx`.

Live E2E, `frontend/scripts/e2e-live.mjs`, with evidence in `docs/screenshots/cc-10/`. The default backend passed **17/17**; the model-failure drill passed **18/18**. The new checks:

- **Duplicate**: at T+10 the candidate is flagged. It is linked from the console, the merged incident's demand disappears from the next plan version, and the flag clears.
- **Medical ID**: a request is denied `CALLER_IS_PATIENT_UNKNOWN`. After the operator confirms yes, the synthetic values show. The event log contains no values, and after closing the dialog they are not on screen.

## Review findings

Resolved: #23-1 (duplicate demand), #23-2 (intake questions, in CC-09), #23-3 (recompute status), #24 (medical path).

Still open for CC-12:

- #21-1: override conflicts without coded reasons;
- #21-2: near-arrival lock ETA;
- #21-3: water rescue reason code;
- #23-3 ID prefixes: `report_N` versus `rpt_`, opaque and documented.

## Known limitations

- Linking does not merge the candidate's triage facts into the original incident. They stay on the merged record for audit.
- E5 similarity is not used; blocking is spatial and time only (150 m, 300 s).
- Simulated hospital pre-alerts are recorded as events but not yet listed in the console.

## Handoff

Next: CC-11 (Claude, independent review and 100-seed evaluation), then CC-12 fixes.
