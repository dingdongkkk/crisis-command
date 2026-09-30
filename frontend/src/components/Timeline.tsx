import type { Incident } from '../contracts'
import { severityLabel, simClock } from '../state/labels'

interface TimelineProps {
  incidents: Incident[]
  simTimeS: number
  selectedId: string | null
  onSelect: (id: string) => void
}

/**
 * Incident arrivals on the simulation clock (T+0 → now), from snapshot data only.
 * Supplementary like the map: the incident queue is the keyboard/screen-reader path.
 */
export function Timeline({ incidents, simTimeS, selectedId, onSelect }: TimelineProps) {
  const span = Math.max(simTimeS, 60)
  const ticks = Array.from({ length: Math.floor(span / 60) + 1 }, (_, m) => m * 60).filter((t) => t % (span > 900 ? 300 : 120) === 0)
  const items = incidents.filter((i) => i.status === 'active')
  return (
    <div className="timeline" aria-hidden="true">
      <span className="kv-label timeline-title">Timeline</span>
      <div className="timeline-track">
        {ticks.map((t) => (
          <span key={t} className="timeline-tick mono" style={{ left: `${(t / span) * 100}%` }}>
            {simClock(t).replace(':00', '')}
          </span>
        ))}
        {items.map((i) => (
          <span
            key={i.incident_id}
            className={`timeline-event sev-${i.severity}${i.incident_id === selectedId ? ' selected' : ''}${i.category !== 'emergency' ? ' non-emergency' : ''}`}
            style={{ left: `${(i.created_sim_time_s / span) * 100}%` }}
            onClick={() => onSelect(i.incident_id)}
            title={`${i.incident_id} · ${severityLabel(i.severity)} · ${simClock(i.created_sim_time_s)}`}
          >
            <span className="timeline-diamond" />
          </span>
        ))}
        <span className="timeline-now mono" style={{ left: '100%' }}>
          NOW {simClock(simTimeS)}
        </span>
      </div>
    </div>
  )
}
