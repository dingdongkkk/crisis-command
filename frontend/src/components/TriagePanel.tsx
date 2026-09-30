import { forwardRef } from 'react'
import type { Incident, TriageFact, TriageFacts } from '../contracts'
import {
  categoryLabel,
  escalationLabel,
  factName,
  factSourceLabel,
  factValueLabel,
  needTypeLabel,
  reasonText,
  severityIcon,
  severityLabel,
} from '../state/labels'

interface TriagePanelProps {
  incident: Incident | null
  facts: TriageFacts | null
}

function valueText(fact: TriageFact): string {
  if (fact.count) {
    if (fact.count.status === 'unknown') return 'UNKNOWN'
    return `${fact.count.value ?? '?'}${fact.count.status === 'approximate' ? ' (approx.)' : ''}`
  }
  return factValueLabel(fact.value)
}

const isUnknown = (fact: TriageFact) => (fact.count ? fact.count.status === 'unknown' : fact.value === 'unknown')

export const TriagePanel = forwardRef<HTMLHeadingElement, TriagePanelProps>(function TriagePanel({ incident, facts }, ref) {
  if (!incident) {
    return (
      <section className="triage" aria-labelledby="triage-title">
        <h2 id="triage-title" className="section-title" ref={ref} tabIndex={-1}>Triage</h2>
        <p className="empty">Select an incident to see its facts.</p>
      </section>
    )
  }
  const applicable = new Set(facts?.applicable_facts ?? [])
  const allFacts = facts?.facts ?? []
  const unknownCritical = allFacts.filter((f) => applicable.has(f.key) && isUnknown(f))
  const escalation = facts?.escalation

  return (
    <section className="triage" aria-labelledby="triage-title">
      <h2 id="triage-title" className="section-title" ref={ref} tabIndex={-1}>
        Triage · {incident.incident_id}
      </h2>
      <p>
        <span className={`sev-badge sev-${incident.severity}`}>
          <span aria-hidden="true">{severityIcon(incident.severity)} </span>
          {severityLabel(incident.severity)}
        </span>{' '}
        {incident.kind.replaceAll('_', ' ')} · {categoryLabel(incident.category)}
      </p>
      {incident.category !== 'emergency' && <p className="notice">No emergency unit needed · {categoryLabel(incident.category)}</p>}
      {escalation?.escalated && (
        <p className="escalated" role="note">
          With operator — reason: {escalation.reasons.map(escalationLabel).join(', ')}
        </p>
      )}
      {!facts ? (
        <p className="empty">No triage facts recorded for this incident.</p>
      ) : (
        <>
          {unknownCritical.length > 0 && (
            <div className="unknown-critical">
              <h3>Not established — treated as present for planning</h3>
              <ul>
                {unknownCritical.map((f) => (
                  <li key={f.key}>{factName(f.key)}: UNKNOWN</li>
                ))}
              </ul>
            </div>
          )}
          <table className="facts">
            <caption className="visually-hidden">Triage facts</caption>
            <thead>
              <tr>
                <th scope="col">Fact</th>
                <th scope="col">Value</th>
                <th scope="col">Source</th>
                <th scope="col">Notes</th>
              </tr>
            </thead>
            <tbody>
              {[...allFacts]
                .sort((a, b) => Number(!(applicable.has(a.key) && isUnknown(a))) - Number(!(applicable.has(b.key) && isUnknown(b))))
                .map((f) => (
                  <tr key={f.key}>
                    <th scope="row">{factName(f.key)}</th>
                    <td className={`fact-${isUnknown(f) ? 'unknown' : f.value ?? 'count'}`}>{valueText(f)}</td>
                    <td>{factSourceLabel(f.source)}</td>
                    <td>
                      {incident.assumed_facts.includes(f.key) && <span className="tag tag-provisional">PROVISIONAL</span>}
                      {f.conflict && <span className="tag tag-conflict">CONFLICT</span>}
                      {f.coerced_from && (
                        <span className="tag" title={f.coercion_reason ?? undefined}>
                          model said {factValueLabel(f.coerced_from)} without evidence
                        </span>
                      )}
                      {f.evidence.map((e) => (
                        <span key={`${e.report_id}-${e.start}`} className="muted evidence">
                          {' '}
                          {e.report_id} chars {e.start}–{e.end}
                        </span>
                      ))}
                      {f.confirmed_by_operator && <span className="tag">CONFIRMED</span>}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </>
      )}
      <h3>Needs</h3>
      {incident.needs.length === 0 ? (
        <p className="empty">No emergency-unit needs.</p>
      ) : (
        <ul className="needs">
          {incident.needs.map((n) => (
            <li key={n.need_id}>
              {needTypeLabel(n.type)} ×{n.quantity}{' '}
              {n.basis === 'provisional_unknown' && <span className="tag tag-provisional">PROVISIONAL</span>}
              {n.reasons.length > 0 && <span className="muted"> — {n.reasons.map(reasonText).join('; ')}</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
})
