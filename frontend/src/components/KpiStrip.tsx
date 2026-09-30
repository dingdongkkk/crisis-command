import type { StateSnapshot } from '../contracts'

/** Counts of server-reported state only; the browser does not recompute any policy. */
export function KpiStrip({ snapshot }: { snapshot: StateSnapshot }) {
  const active = snapshot.incidents.filter((i) => i.category === 'emergency' && i.status === 'active')
  const critical = active.filter((i) => i.severity === 'critical').length
  const available = snapshot.units.filter((u) => u.status === 'available' || u.status === 'returning').length
  const plan = snapshot.current_proposal ?? snapshot.approved_plan
  const unmet = plan?.unmet_needs.reduce((n, u) => n + u.quantity_unmet, 0) ?? 0
  const uncovered = plan?.coverage.filter((c) => c.status !== 'covered').length ?? 0
  const outOfService = snapshot.units.filter((u) => ['broken_down', 'out_of_service', 'off_duty'].includes(u.status)).length
  const cells = [
    { label: 'Emergencies', value: String(active.length), tone: '' },
    { label: 'Critical', value: String(critical), tone: critical > 0 ? 'danger' : '' },
    { label: 'Units free', value: `${available}/${snapshot.units.length}`, tone: available === 0 ? 'warning' : '' },
    { label: 'Out of service', value: String(outOfService), tone: outOfService > 0 ? 'danger' : '' },
    { label: 'Unmet needs', value: String(unmet), tone: unmet > 0 ? 'danger' : 'success' },
    { label: 'Zones uncovered', value: String(uncovered), tone: uncovered > 0 ? 'warning' : 'success' },
  ]
  return (
    <ul className="statbar" aria-label="Situation summary">
      {cells.map((c, index) => (
        <li key={c.label} className={`stat${c.tone ? ` stat-${c.tone}` : ''}`}>
          <span className="stat-index mono" aria-hidden="true">0{index + 1}</span>
          <span className="kv-label">{c.label}</span>
          <span className="stat-value mono">{c.value}</span>
        </li>
      ))}
    </ul>
  )
}
