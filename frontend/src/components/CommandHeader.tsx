import { Crosshair, Layers, Radio, ScanLine } from 'lucide-react'
import type { StateSnapshot } from '../contracts'

/** Operational context from the current snapshot; decorative marks are not telemetry. */
export function CommandHeader({ snapshot }: { snapshot: StateSnapshot }) {
  return (
    <section className="command-header" aria-label="Operations overview">
      <div className="command-heading">
        <div className="command-eyebrow">City response / Bengaluru</div>
        <h2>Operations overview<span>.</span></h2>
      </div>
      <div className="command-context">
        <span><Crosshair size={15} aria-hidden="true" /><span>Area of operations<strong>Bengaluru Metro</strong></span></span>
        <span><Layers size={15} aria-hidden="true" /><span>Snapshot<strong className="mono">#{String(snapshot.as_of_sequence).padStart(5, '0')}</strong></span></span>
        <span className="command-mode"><ScanLine size={18} aria-hidden="true" /><span>Decision support<strong>Human-in-the-loop</strong></span></span>
      </div>
    </section>
  )
}

export function CommandFooter({ sessionId }: { sessionId: string }) {
  return (
    <footer className="command-footer mono">
      <span><Radio size={11} aria-hidden="true" /> Crisis Command · Simulation environment</span>
      <span>{sessionId} <span className="footer-divider">/</span> Synthetic data</span>
    </footer>
  )
}
