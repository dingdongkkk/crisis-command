import type { Incident, Plan } from '../contracts'
import { categoryLabel, severityIcon, severityLabel, simClock } from '../state/labels'
import { sortEmergencies } from '../state/queue'
import { IncidentKindIcon } from './icons'

interface IncidentQueueProps {
  incidents: Incident[]
  proposal: Plan | null
  selectedId: string | null
  onSelect: (id: string) => void
}

export function IncidentQueue({ incidents, proposal, selectedId, onSelect }: IncidentQueueProps) {
  const emergencies = sortEmergencies(incidents)
  const others = incidents.filter((i) => i.category !== 'emergency' && i.status === 'active')
  const unmetByIncident = new Map<string, string[]>()
  for (const n of proposal?.unmet_needs ?? []) {
    unmetByIncident.set(n.incident_id, [...(unmetByIncident.get(n.incident_id) ?? []), n.type.toUpperCase()])
  }

  return (
    <section className="rail-section" aria-labelledby="queue-title">
      <h2 id="queue-title" className="section-title">
        Incidents <span className="count">({emergencies.length})</span>
        <span className="section-hint">by severity, then waiting</span>
      </h2>
      {emergencies.length === 0 ? (
        <p className="empty">No active emergency incidents.</p>
      ) : (
        <ol className="queue" aria-label="Emergency incidents, most severe first">
          {emergencies.map((incident) => {
            const unmet = unmetByIncident.get(incident.incident_id)
            const selected = incident.incident_id === selectedId
            return (
              <li key={incident.incident_id}>
                <button
                  type="button"
                  className={`queue-item sev-${incident.severity}${selected ? ' selected' : ''}`}
                  aria-current={selected ? 'true' : undefined}
                  data-incident-id={incident.incident_id}
                  onClick={() => onSelect(incident.incident_id)}
                >
                  <span className="queue-line">
                    <span className="queue-icon" aria-hidden="true"><IncidentKindIcon kind={incident.kind} size={14} /></span>
                    <span className="queue-main">
                      <strong>{incident.kind.replaceAll('_', ' ')}</strong>
                    </span>
                    <span className="mono queue-id">{incident.incident_id}</span>
                  </span>
                  <span className="queue-meta">
                    <span className="sev-badge">
                      <span aria-hidden="true">{severityIcon(incident.severity)} </span>
                      {severityLabel(incident.severity)}
                    </span>
                    <span className="muted mono"> · since {simClock(incident.created_sim_time_s)}</span>
                  </span>
                  {(incident.assumed_facts.length > 0 || unmet) && (
                    <span className="tags">
                      {incident.assumed_facts.length > 0 && <span className="tag tag-provisional">PROVISIONAL</span>}
                      {unmet?.map((t) => (
                        <span key={t} className="tag tag-unmet">{t} UNMET</span>
                      ))}
                    </span>
                  )}
                </button>
              </li>
            )
          })}
        </ol>
      )}
      <details className="non-emergency">
        <summary>Non-emergency ({others.length})</summary>
        {others.length === 0 ? (
          <p className="empty">None.</p>
        ) : (
          <ul>
            {others.map((i) => (
              <li key={i.incident_id}>
                <button type="button" className="link" onClick={() => onSelect(i.incident_id)}>
                  {i.incident_id}
                </button>{' '}
                — No emergency unit needed · {categoryLabel(i.category)}
              </li>
            ))}
          </ul>
        )}
      </details>
    </section>
  )
}
