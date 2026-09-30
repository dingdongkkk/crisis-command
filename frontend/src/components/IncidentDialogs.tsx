import { useState } from 'react'
import type { ConsoleApi, MedicalValues } from '../api/types'
import type { Incident, StateSnapshot } from '../contracts'
import { factValueLabel, kindLabel } from '../state/labels'
import { Dialog } from './Dialog'

type IncidentApi = NonNullable<ConsoleApi['incidents']>

/** 0008 denial reasons, as operator-facing text. Unknown codes are shown verbatim. */
const DENIAL: Record<string, string> = {
  NO_CONSENT: 'The caller has not consented to share this Medical ID.',
  CONSENT_REVOKED: 'The caller revoked consent for this Medical ID.',
  CALLER_IS_NOT_PATIENT: 'The caller is not the patient.',
  CALLER_IS_PATIENT_UNKNOWN: 'It is not confirmed that the caller is the patient. Confirm it first.',
  INCIDENT_NOT_ACTIVE: 'The incident is not active.',
  PROFILE_NOT_LINKED: 'This Medical ID is not linked to this incident.',
  MISSING_OPERATOR_REASON: 'A reason is required.',
}

const FIELD_LABEL: Record<string, string> = {
  conditions: 'Conditions',
  medications: 'Medications',
  allergies: 'Allergies',
  emergency_contacts: 'Emergency contacts',
}

/**
 * Operator decision on a possible duplicate (0007 AS-07). Never automatic: linking merges the
 * newer report into the original incident; keeping separate clears the flag.
 */
export function DuplicateDialog({ api, snapshot, candidate, onClose, onDone }: {
  api: IncidentApi
  snapshot: StateSnapshot
  candidate: Incident
  onClose: () => void
  onDone: (message: string) => void
}) {
  const originalId = candidate.duplicate_candidate_of[0] ?? ''
  const original = snapshot.incidents.find((i) => i.incident_id === originalId)
  const reportId = candidate.report_ids[0] ?? ''
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (resolution: 'linked' | 'kept_separate') => {
    setBusy(true)
    const result = await api.resolveDuplicate(
      originalId,
      reportId,
      { expected_session_id: snapshot.session_id, resolution, reason_text: reason.trim() },
      crypto.randomUUID(),
    )
    setBusy(false)
    if (!result.ok) {
      setError(result.problem.title)
      return
    }
    onDone(
      resolution === 'linked'
        ? `${candidate.incident_id} linked to ${originalId} as the same emergency. Replanning.`
        : `${candidate.incident_id} kept separate from ${originalId}. Replanning.`,
    )
  }

  return (
    <Dialog title="Possible duplicate" onClose={onClose}>
      <p>
        <strong>{candidate.incident_id}</strong> ({kindLabel(candidate.kind)}) was reported near{' '}
        <strong>{originalId}</strong>
        {original ? ` (${kindLabel(original.kind)})` : ''} within minutes. Until you decide, both are planned for, and the
        plan carries an acknowledgement flag.
      </p>
      {error && <p className="notice notice-error" role="alert">Not recorded: {error}</p>}
      <label>
        Reason (required, no medical detail)
        <textarea maxLength={280} value={reason} onChange={(e) => setReason(e.target.value)} />
      </label>
      <div className="dialog-actions">
        <button type="button" onClick={onClose}>Cancel</button>
        <button type="button" disabled={busy || !reason.trim() || !reportId} onClick={() => void submit('kept_separate')}>
          Different emergencies — keep separate
        </button>
        <button type="button" className="primary" disabled={busy || !reason.trim() || !reportId} onClick={() => void submit('linked')}>
          Same emergency — link
        </button>
      </div>
    </Dialog>
  )
}

/**
 * Consent-gated synthetic Medical ID (0008 AS-50). The operator first confirms whether the
 * caller is the patient; values are displayed only inside this dialog and discarded on close.
 */
export function MedicalIdDialog({ api, snapshot, incident, onClose }: {
  api: IncidentApi
  snapshot: StateSnapshot
  incident: Incident
  onClose: () => void
}) {
  const facts = snapshot.triage_facts.find((f) => f.incident_id === incident.incident_id)
  const patient = facts?.facts.find((f) => f.key === 'caller_is_patient')?.value ?? 'unknown'
  const [profileRef, setProfileRef] = useState('')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [values, setValues] = useState<MedicalValues | null>(null)

  const confirm = async (value: 'yes' | 'no') => {
    setBusy(true)
    const result = await api.confirmFact(
      incident.incident_id,
      'caller_is_patient',
      { expected_session_id: snapshot.session_id, value, reason_text: 'Operator asked the caller' },
      crypto.randomUUID(),
    )
    setBusy(false)
    setError(result.ok ? null : result.problem.title)
  }

  const request = async () => {
    setBusy(true)
    setValues(null)
    const result = await api.medicalAccess(
      incident.incident_id,
      { expected_session_id: snapshot.session_id, profile_ref: profileRef.trim(), operator_reason: reason.trim() },
      crypto.randomUUID(),
    )
    setBusy(false)
    if (result.ok) {
      setError(null)
      setValues(result.body)
      return
    }
    const code = (result.problem as { reason?: string }).reason
    setError(code ? `${DENIAL[code] ?? code} (${code})` : result.problem.title)
  }

  return (
    <Dialog title={`Medical ID · ${incident.incident_id}`} onClose={onClose}>
      <p className="muted">
        Synthetic profiles only. Access needs the caller&apos;s consent, the caller to be the patient, an active incident
        and your reason; every attempt is audited without the values.
      </p>
      <div className="kv-row">
        <span className="kv-label">Caller is the patient</span>{' '}
        <strong>{factValueLabel(patient)}</strong>
        <span className="question-actions inline">
          <button type="button" disabled={busy || patient === 'yes'} onClick={() => void confirm('yes')}>Confirm yes</button>
          <button type="button" disabled={busy || patient === 'no'} onClick={() => void confirm('no')}>Confirm no</button>
        </span>
      </div>
      <label>
        Medical ID reference (from the caller)
        <input value={profileRef} onChange={(e) => setProfileRef(e.target.value)} placeholder="e.g. mprof_syn_0001" />
      </label>
      <label>
        Reason for access (required)
        <textarea maxLength={280} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Check allergies before treatment advice" />
      </label>
      {error && <p className="notice notice-error" role="alert">Access denied: {error}</p>}
      {values && (
        <div className="medical-values" role="region" aria-label="Medical ID values">
          <p className="kv-label">SYNTHETIC · shown once · not stored</p>
          {Object.entries(values.values).map(([field, items]) => (
            <p key={field}>
              <strong>{FIELD_LABEL[field] ?? field}:</strong> {(items ?? []).join(', ') || '—'}
            </p>
          ))}
        </div>
      )}
      <div className="dialog-actions">
        <button type="button" onClick={onClose}>Close</button>
        <button type="button" className="primary" disabled={busy || !profileRef.trim() || !reason.trim()} onClick={() => void request()}>
          Request access
        </button>
      </div>
    </Dialog>
  )
}
