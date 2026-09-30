import { Play, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import { DEMO_STEPS, type ConsoleApi } from '../api/types'
import { currentStep } from '../state/scenario'
import type { StateSnapshot } from '../contracts'
import { Dialog } from './Dialog'

interface ScenarioControlsProps {
  api: NonNullable<ConsoleApi['simulation']>
  snapshot: StateSnapshot
  disabled: boolean
  onNotice: (message: string) => void
}

export function ScenarioControls({ api, snapshot, disabled, onNotice }: ScenarioControlsProps) {
  const [busy, setBusy] = useState(false)
  const [confirmReset, setConfirmReset] = useState(false)
  const current = currentStep(snapshot)
  const index = current ? DEMO_STEPS.findIndex((s) => s.step === current) : -1
  const next = DEMO_STEPS[index + 1]

  const run = async (action: () => Promise<{ ok: boolean; problem?: { title: string; code: string } }>, label: string) => {
    setBusy(true)
    const result = await action()
    setBusy(false)
    if (!result.ok && result.problem) onNotice(`${label} failed: ${result.problem.title} (${result.problem.code})`)
  }

  return (
    <div className="scenario" aria-label="Simulation scenario">
      <span className="kv-label">Scenario</span>
      <ol className="scenario-steps">
        {DEMO_STEPS.map((s, i) => (
          <li key={s.step} className={i <= index ? 'done' : i === index + 1 ? 'next' : ''}>
            <span className="mono">{s.step}</span>
          </li>
        ))}
      </ol>
      <button
        type="button"
        className="scenario-btn"
        disabled={disabled || busy || !next}
        onClick={() => next && void run(() => api.advance(next.step, snapshot.session_id, crypto.randomUUID()), `Advance to ${next.step}`)}
      >
        <Play size={13} aria-hidden="true" /> {next ? `Advance to ${next.step}` : 'Scenario complete'}
      </button>
      <button type="button" className="icon-btn" aria-label="Reset simulation" disabled={disabled || busy} onClick={() => setConfirmReset(true)}>
        <RotateCcw size={15} />
      </button>
      {confirmReset && (
        <Dialog title="Reset the simulation?" onClose={() => setConfirmReset(false)}>
          <p>This starts a new simulation session from the seeded Bengaluru world. The current session's history is kept for audit; pending simulated dispatches are cancelled.</p>
          <div className="dialog-actions">
            <button type="button" onClick={() => setConfirmReset(false)}>Cancel</button>
            <button
              type="button"
              className="primary"
              onClick={() => {
                setConfirmReset(false)
                void run(() => api.reset(snapshot.session_id, crypto.randomUUID()), 'Reset')
              }}
            >
              Reset simulation
            </button>
          </div>
        </Dialog>
      )}
    </div>
  )
}
