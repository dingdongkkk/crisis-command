import { ArrowLeft, ArrowRight, BrainCircuit, Clock3, Crosshair, Radio, Route, ShieldCheck, UserCheck } from 'lucide-react'
import { type KeyboardEvent as ReactKeyboardEvent, useEffect, useRef, useState } from 'react'

interface DemoTourProps {
  onFinish: () => void
}

const steps = [
  {
    code: 'MISSION_01',
    eyebrow: 'Welcome to Crisis Command',
    title: 'A city in motion. One human in command.',
    body: 'A synthetic Bengaluru emergency unfolds over ten simulated minutes. Language models may understand and explain; deterministic rules and optimisation allocate; a human approves every risky change.',
    kind: 'mission',
  },
  {
    code: 'SYSTEM_02',
    eyebrow: 'How decisions are made',
    title: 'From caller words to an auditable plan.',
    body: 'The console keeps language understanding, hard safety constraints and operator authority visibly separate.',
    kind: 'flow',
  },
  {
    code: 'SCENARIO_03',
    eyebrow: 'The ten-minute scenario',
    title: 'Pressure rises at every step.',
    body: 'Use the Advance control in order. Each stage adds a new operational constraint and forces the plan to explain what changed.',
    kind: 'timeline',
  },
  {
    code: 'OPERATOR_04',
    eyebrow: 'Your demo controls',
    title: 'Show judgment, not automation theatre.',
    body: 'Select incidents, inspect evidence, acknowledge explicit risks, then approve only the plan you reviewed. Every dispatch shown is simulated.',
    kind: 'controls',
  },
] as const

function StepVisual({ kind }: { kind: (typeof steps)[number]['kind'] }) {
  if (kind === 'mission') {
    return (
      <div className="tour-mission-grid">
        <div><ShieldCheck size={19} /><span>Simulation only</span><strong>No real dispatch path</strong></div>
        <div><UserCheck size={19} /><span>Human authority</span><strong>Every risky plan is approved</strong></div>
        <div><Radio size={19} /><span>Live state</span><strong>Events replay in sequence</strong></div>
      </div>
    )
  }
  if (kind === 'flow') {
    const items = [
      [Radio, '01', 'Caller intake', 'English, Hindi or Hinglish text'],
      [BrainCircuit, '02', 'Structured facts', 'Evidence retained; unknown stays unknown'],
      [Route, '03', 'Safe allocation', 'Routes, eligibility, capacity and locks'],
      [UserCheck, '04', 'Operator approval', 'Diffs and flags before simulated dispatch'],
    ] as const
    return (
      <div className="tour-flow">
        {items.map(([Icon, code, label, detail], index) => (
          <div className="tour-flow-item" key={code}>
            <span className="tour-flow-code mono">{code}</span>
            <Icon size={21} aria-hidden="true" />
            <strong>{label}</strong>
            <span>{detail}</span>
            {index < items.length - 1 && <ArrowRight className="tour-flow-arrow" size={15} aria-hidden="true" />}
          </div>
        ))}
      </div>
    )
  }
  if (kind === 'timeline') {
    const moments = [
      ['T+0', 'Cardiac emergency', 'Non-emergency calls filtered out'],
      ['T+2', 'Accident + gas leak', 'Units compete; on-scene lock holds'],
      ['T+5', 'Flood + duplicate', 'Unreachable needs stay explicit'],
      ['T+10', 'Breakdown + collapse', 'Critical ALS shortage surfaces'],
    ]
    return (
      <ol className="tour-timeline">
        {moments.map(([time, title, detail]) => (
          <li key={time}>
            <span className="tour-time mono"><Clock3 size={13} />{time}</span>
            <strong>{title}</strong>
            <span>{detail}</span>
          </li>
        ))}
      </ol>
    )
  }
  return (
    <div className="tour-controls">
      <div><span className="tour-control-index mono">01</span><strong>Advance the scenario</strong><p>Move through T+0, T+2, T+5 and T+10 in order.</p></div>
      <div><span className="tour-control-index mono">02</span><strong>Inspect the evidence</strong><p>Select an incident to see facts, uncertainty, needs and road candidates.</p></div>
      <div><span className="tour-control-index mono">03</span><strong>Read the plan diff</strong><p>Show added, moved, released and unmet needs before acting.</p></div>
      <div><span className="tour-control-index mono">04</span><strong>Approve deliberately</strong><p>Acknowledge every risk, then confirm simulated dispatch.</p></div>
    </div>
  )
}

export function DemoTour({ onFinish }: DemoTourProps) {
  const [index, setIndex] = useState(0)
  const actionRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLElement>(null)
  const step = steps[index] ?? steps[0]
  const last = index === steps.length - 1

  useEffect(() => {
    actionRef.current?.focus()
  }, [index])

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight' && !last) setIndex((value) => Math.min(value + 1, steps.length - 1))
      if (event.key === 'ArrowLeft' && index > 0) setIndex((value) => Math.max(value - 1, 0))
      if (event.key === 'Escape') onFinish()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKey)
    }
  }, [index, last, onFinish])

  const keepFocusInside = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.key !== 'Tab') return
    const controls = Array.from(dialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled])') ?? [])
    const first = controls.at(0)
    const final = controls.at(-1)
    if (!first || !final) return
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      final.focus()
    } else if (!event.shiftKey && document.activeElement === final) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    <div className="tour-backdrop">
      <section ref={dialogRef} className="tour-dialog" role="dialog" aria-modal="true" aria-labelledby="tour-title" onKeyDown={keepFocusInside}>
        <header className="tour-header">
          <div className="tour-wordmark"><span className="tour-mark"><Crosshair size={17} /></span><span>CRISIS COMMAND<strong>DEMO PREFLIGHT</strong></span></div>
          <button type="button" className="tour-skip" onClick={onFinish}>Skip guide</button>
        </header>
        <div className="tour-progress" aria-label={`Tour step ${index + 1} of ${steps.length}`}>
          {steps.map((item, itemIndex) => <i key={item.code} className={itemIndex <= index ? 'complete' : ''} />)}
        </div>
        <div className="tour-content">
          <div className="tour-copy">
            <span className="tour-code mono">{step.code} / {String(index + 1).padStart(2, '0')}</span>
            <p className="tour-eyebrow">{step.eyebrow}</p>
            <h2 id="tour-title">{step.title}</h2>
            <p className="tour-body">{step.body}</p>
          </div>
          <StepVisual kind={step.kind} />
        </div>
        <footer className="tour-actions">
          <span className="tour-safety"><ShieldCheck size={14} /> Synthetic data · simulated dispatch</span>
          <div>
            {index > 0 && <button type="button" className="tour-back" onClick={() => setIndex((value) => value - 1)}><ArrowLeft size={14} /> Back</button>}
            <button ref={actionRef} type="button" className="tour-next" onClick={() => last ? onFinish() : setIndex((value) => value + 1)}>
              {last ? 'Enter command centre' : 'Continue'} {last ? <Crosshair size={14} /> : <ArrowRight size={14} />}
            </button>
          </div>
        </footer>
      </section>
    </div>
  )
}
