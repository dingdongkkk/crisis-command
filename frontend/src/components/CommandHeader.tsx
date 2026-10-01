import { Crosshair, Layers, Radio, ScanLine } from 'lucide-react'
import type { StateSnapshot } from '../contracts'

/** Operational context from the current snapshot; decorative marks are not telemetry. */
export function CommandHeader({ snapshot }: { snapshot: StateSnapshot }) {
  return (
    <section className="command-header" aria-label="Operations overview">
      <div className="command-heading">
        <div className="command-eyebrow">BLR_01 / ACTIVE RESPONSE</div>
        <h2>City command<span>.</span></h2>
      </div>
      <div className="command-context">
        <span><Crosshair size={14} aria-hidden="true" /><span>Area of operations<strong>Bengaluru Metro</strong></span></span>
        <span><Layers size={14} aria-hidden="true" /><span>Data sequence<strong className="mono">#{String(snapshot.as_of_sequence).padStart(5, '0')}</strong></span></span>
        <span className="command-mode"><ScanLine size={16} aria-hidden="true" /><span>Control mode<strong>Human-in-the-loop</strong></span></span>
      </div>
    </section>
  )
}

export function CommandFooter({ sessionId }: { sessionId: string }) {
  return (
    <footer className="command-footer mono">
      <span><Radio size={10} aria-hidden="true" /> Crisis Command / Simulation environment</span>
      <span>{sessionId} <span className="footer-divider">/</span> Synthetic data</span>
    </footer>
  )
}
