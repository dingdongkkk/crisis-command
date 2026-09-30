import { Crosshair, Layers, Radio, ScanLine } from 'lucide-react'
import type { StateSnapshot } from '../contracts'

/** Operational context from the current snapshot; decorative marks are not telemetry. */
export function CommandHeader({ snapshot }: { snapshot: StateSnapshot }) {
  return (
    <section className="command-header" aria-label="Operations overview">
      <div className="command-heading">
        <div className="command-eyebrow mono"><span className="signal-dash" /> BENGALURU / OPERATIONS THEATRE</div>
        <h2>Every second. <span>One command.</span></h2>
      </div>
      <div className="command-context">
        <span><Crosshair size={15} aria-hidden="true" /><span>AREA OF OPERATIONS<strong>Bengaluru Metro</strong></span></span>
        <span><Layers size={15} aria-hidden="true" /><span>EVENT SNAPSHOT<strong className="mono">SEQ / {String(snapshot.as_of_sequence).padStart(5, '0')}</strong></span></span>
        <span className="command-mode"><ScanLine size={18} aria-hidden="true" /><span>DECISION SUPPORT<strong>Human-in-the-loop</strong></span></span>
      </div>
    </section>
  )
}

export function CommandFooter({ sessionId }: { sessionId: string }) {
  return (
    <footer className="command-footer mono">
      <span><Radio size={11} aria-hidden="true" /> CRISIS COMMAND / SIMULATION ENVIRONMENT</span>
      <span>{sessionId} <span className="footer-divider">/</span> SYNTHETIC DATA</span>
    </footer>
  )
}
