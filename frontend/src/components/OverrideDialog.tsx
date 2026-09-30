import { useState } from 'react'
import type { ApiResult } from '../api/types'
import type { OverrideCommand, OverrideRecorded, Plan, Problem, StateSnapshot } from '../contracts'
import { conflictText, unitStatusLabel, unitTypeLabel } from '../state/labels'
import { Dialog } from './Dialog'

type Kind = 'pin' | 'forbid' | 'hold_unit' | 'approve_bls_bridge'
export type OverridePrefill = { kind: 'approve_bls_bridge'; unitId: string; needId: string }
type Submit = (
  command: Omit<OverrideCommand, 'expected_session_id' | 'expected_plan_id' | 'expected_planning_sequence'>,
) => Promise<ApiResult<OverrideRecorded>>

const KIND_LABEL: Record<Kind, string> = {
  pin: 'Pin a unit to a need',
  forbid: 'Forbid a unit from an incident',
  hold_unit: 'Hold a unit in reserve',
  approve_bls_bridge: 'BLS bridge for an unmet ALS need',
}

interface OverrideDialogProps {
  snapshot: StateSnapshot
  plan: Plan
  prefill?: OverridePrefill
  onSubmit: Submit
  onClose: () => void
}

type Phase =
  | { kind: 'editing' }
  | { kind: 'submitting' }
  | { kind: 'rejected'; problem: Problem }
  | { kind: 'accepted'; overrideId: string }

export function OverrideDialog({ snapshot, plan, prefill, onSubmit, onClose }: OverrideDialogProps) {
  const [kind, setKind] = useState<Kind>(prefill?.kind ?? 'pin')
  const [unitId, setUnitId] = useState(prefill?.unitId ?? '')
  const [needId, setNeedId] = useState(prefill?.needId ?? '')
  const [incidentId, setIncidentId] = useState('')
  const [reason, setReason] = useState('')
  const [phase, setPhase] = useState<Phase>({ kind: 'editing' })

  const needs = snapshot.incidents.flatMap((i) => i.needs.map((n) => ({ ...n, incident_id: i.incident_id })))
  const alsUnmet = plan.unmet_needs.filter((n) => n.type === 'als')
  const needChoices = kind === 'approve_bls_bridge' ? alsUnmet.map((n) => n.need_id) : needs.map((n) => n.need_id)
  const needsTarget = kind === 'pin' || kind === 'approve_bls_bridge'
  const complete = unitId && reason.trim() && (!needsTarget || needId) && (kind !== 'forbid' || incidentId)

  const submit = async () => {
    setPhase({ kind: 'submitting' })
    const base = { kind, unit_id: unitId, reason_text: reason.trim() }
    const command =
      kind === 'pin' ? { ...base, need_id: needId }
      : kind === 'forbid' ? { ...base, incident_id: incidentId }
      : kind === 'approve_bls_bridge' ? { ...base, bridges_need_id: needId }
      : base
    const result = await onSubmit(command)
    setPhase(result.ok ? { kind: 'accepted', overrideId: result.body.override_id } : { kind: 'rejected', problem: result.problem })
  }

  if (phase.kind === 'accepted') {
    return (
      <Dialog title="Override recorded" onClose={onClose}>
        <p role="status">Override {phase.overrideId} recorded. Recomputing plan… The new proposal still needs your approval.</p>
        <div className="dialog-actions">
          <button type="button" className="primary" onClick={onClose}>Close</button>
        </div>
      </Dialog>
    )
  }

  const stale = phase.kind === 'rejected' && (phase.problem.code === 'STALE_PLAN' || phase.problem.code === 'STALE_SESSION')
  return (
    <Dialog title="Override" onClose={onClose}>
      <p className="muted">Overrides constrain the next plan. They never bypass locks, availability, type, route or capacity rules.</p>
      {phase.kind === 'rejected' && (
        <div className="notice notice-error" role="alert">
          {stale ? (
            <p>World changed before your override was recorded. Review and retry. Nothing was applied.</p>
          ) : (
            <>
              <p>Override rejected — nothing was applied.</p>
              <ul>
                {((phase.problem.conflicts ?? []) as { code: string; unit_id?: string | null; detail: string }[]).map((c, i) => (
                  <li key={i}>{conflictText(c)}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
      <fieldset disabled={phase.kind === 'submitting'}>
        <label>
          Kind
          <select value={kind} onChange={(e) => setKind(e.target.value as Kind)}>
            {(Object.keys(KIND_LABEL) as Kind[]).map((k) => (
              <option key={k} value={k}>{KIND_LABEL[k]}</option>
            ))}
          </select>
        </label>
        <label>
          Unit
          <select value={unitId} onChange={(e) => setUnitId(e.target.value)}>
            <option value="">Choose a unit</option>
            {snapshot.units.map((u) => (
              <option key={u.unit_id} value={u.unit_id}>
                {u.display_name} · {unitTypeLabel(u.type)} · {unitStatusLabel(u.status)}
              </option>
            ))}
          </select>
        </label>
        {needsTarget && (
          <label>
            {kind === 'approve_bls_bridge' ? 'Unmet ALS need' : 'Need'}
            <select value={needId} onChange={(e) => setNeedId(e.target.value)}>
              <option value="">Choose a need</option>
              {needChoices.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        )}
        {kind === 'forbid' && (
          <label>
            Incident
            <select value={incidentId} onChange={(e) => setIncidentId(e.target.value)}>
              <option value="">Choose an incident</option>
              {snapshot.incidents.map((i) => <option key={i.incident_id} value={i.incident_id}>{i.incident_id}</option>)}
            </select>
          </label>
        )}
        <label>
          Reason (required, no medical detail)
          <textarea required maxLength={280} value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
      </fieldset>
      <div className="dialog-actions">
        <button type="button" className="primary" disabled={!complete || phase.kind === 'submitting'} onClick={submit}>
          {phase.kind === 'submitting' ? 'Submitting…' : 'Submit override'}
        </button>
        <button type="button" onClick={onClose}>Cancel</button>
      </div>
    </Dialog>
  )
}
