import { useState } from 'react'
import type { Incident, Plan } from '../contracts'
import { flagSeverityLabel, flagSubject } from '../state/labels'
import { Dialog } from './Dialog'

interface ApproveDialogProps {
  plan: Plan
  incidents: Incident[]
  onConfirm: (note: string) => void
  onCancel: () => void
}

export function ApproveDialog({ plan, incidents, onConfirm, onCancel }: ApproveDialogProps) {
  const [note, setNote] = useState('')
  const { totals } = plan.diff
  return (
    <Dialog title={`Approve plan v${plan.version}?`} onClose={onCancel}>
      <p>
        This sends <strong>simulated</strong> dispatch commands only. No real vehicle, call or notification is involved.
      </p>
      <ul>
        <li>{totals.units_added} unit(s) newly assigned, {totals.units_moved} moved, {totals.units_released} released</li>
        <li>{totals.needs_unmet} need(s) remain unmet; {totals.zones_uncovered} reserve zone(s) uncovered</li>
      </ul>
      {plan.flags.filter((f) => f.requires_ack).length > 0 && (
        <>
          <h3>You acknowledged</h3>
          <ul>
            {plan.flags.filter((f) => f.requires_ack).map((f) => (
              <li key={f.flag_id}>
                {flagSeverityLabel(f.severity)}: {f.message}
                {flagSubject(f, incidents) && ` — ${flagSubject(f, incidents)}`}
              </li>
            ))}
          </ul>
        </>
      )}
      <label>
        Note (optional, no medical detail)
        <textarea maxLength={280} value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <div className="dialog-actions">
        <button type="button" className="primary" onClick={() => onConfirm(note.trim())}>
          Approve &amp; dispatch (simulated)
        </button>
        <button type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </Dialog>
  )
}
