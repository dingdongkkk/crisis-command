import { useState } from 'react'
import type { ConsoleApi } from '../api/types'
import type { ReportAccepted, StateSnapshot } from '../contracts'
import { DEMO_PLACES } from '../state/scenario'
import { Dialog } from './Dialog'

interface ReportDialogProps {
  api: NonNullable<ConsoleApi['reports']>
  snapshot: StateSnapshot
  onClose: () => void
  onCreated: (result: ReportAccepted) => void
}

/** Simulated caller text → live intake (`POST /reports`). Synthetic data only. */
export function ReportDialog({ api, snapshot, onClose, onCreated }: ReportDialogProps) {
  const [text, setText] = useState('')
  const [place, setPlace] = useState(0)
  const [phase, setPhase] = useState<{ kind: 'editing' | 'submitting' } | { kind: 'error'; message: string }>({ kind: 'editing' })

  const submit = async () => {
    setPhase({ kind: 'submitting' })
    const location = DEMO_PLACES[place] ?? DEMO_PLACES[0]
    if (!location) return
    const result = await api.submit(
      {
        expected_session_id: snapshot.session_id,
        channel: 'text_sim',
        text: text.trim(),
        location: { type: 'Point', coordinates: location.coordinates },
        location_source: 'caller_stated',
        sim_time_s: snapshot.sim_time_s,
      },
      crypto.randomUUID(),
    )
    if (result.ok) {
      onCreated(result.body)
      onClose()
    } else {
      setPhase({ kind: 'error', message: `${result.problem.title} (${result.problem.code})` })
    }
  }

  return (
    <Dialog title="Simulated call" onClose={onClose}>
      <p className="muted">Type what a (synthetic) caller says, in English, Hindi or Hinglish. Rules extract facts with evidence; nothing is sent anywhere real.</p>
      {phase.kind === 'error' && <p className="notice notice-error" role="alert">Report not recorded: {phase.message}</p>}
      <label>
        Caller text
        <textarea value={text} maxLength={2000} onChange={(e) => setText(e.target.value)} placeholder="e.g. bhai accident ho gaya, do log ghayal hain, khoon beh raha hai" />
      </label>
      <label>
        Location
        <select value={place} onChange={(e) => setPlace(Number(e.target.value))}>
          {DEMO_PLACES.map((p, i) => (
            <option key={p.label} value={i}>{p.label}</option>
          ))}
        </select>
      </label>
      <div className="dialog-actions">
        <button type="button" onClick={onClose}>Cancel</button>
        <button type="button" className="primary" disabled={!text.trim() || phase.kind === 'submitting'} onClick={() => void submit()}>
          {phase.kind === 'submitting' ? 'Recording…' : 'Record call'}
        </button>
      </div>
    </Dialog>
  )
}
