import type { StateSnapshot } from '../contracts'

/** Counts of server-reported state only; the browser does not recompute any policy. */
export function KpiStrip({ snapshot }: { snapshot: StateSnapshot }) {
  const active = snapshot.incidents.filter((i) => i.category === 'emergency' && i.status === 'active')
  const critical = active.filter((i) => i.severity === 'critical').length
  const available = snapshot.units.filter((u) => u.status === 'available' || u.status === 'returning').length
  const plan = snapshot.current_proposal ?? snapshot.approved_plan
  const unmet = plan?.unmet_needs.reduce((n, u) => n + u.quantity_unmet, 0) ?? 0
  const demand = active.reduce((n, i) => n + i.needs.reduce((m, need) => m + need.quantity, 0), 0)
  const uncovered = plan?.coverage.filter((c) => c.status !== 'covered').length ?? 0
  const outOfService = snapshot.units.filter((u) => ['broken_down', 'out_of_service', 'off_duty'].includes(u.status)).length
  const cells: { label: string; value: string; tone: string; bar?: number }[] = [
    { label: 'Emergencies', value: String(active.length), tone: '' },
    { label: 'Critical', value: String(critical), tone: critical > 0 ? 'danger' : '' },
    { label: 'Units free', value: `${available}/${snapshot.units.length}`, tone: available === 0 ? 'warning' : '', bar: snapshot.units.length ? available / snapshot.units.length : 0 },
    { label: 'Out of service', value: String(outOfService), tone: outOfService > 0 ? 'danger' : '' },
    { label: 'Unmet needs', value: String(unmet), tone: unmet > 0 ? 'danger' : 'success', bar: demand ? (demand - Math.min(unmet, demand)) / demand : 1 },
    { label: 'Zones uncovered', value: String(uncovered), tone: uncovered > 0 ? 'warning' : 'success' },
  ]
  return (
    <ul className="statbar" aria-label="Situation summary">
      {cells.map((c) => (
        <li key={c.label} className={`stat${c.tone ? ` stat-${c.tone}` : ''}`}>
          <span className="kv-label">{c.label.toUpperCase().replaceAll(' ', '_')}</span>
          <span className="stat-value mono">{c.value}</span>
          {c.bar !== undefined && (
            <span className="ds-bar" aria-hidden="true" title={c.label === 'Unmet needs' ? 'Share of demand met' : 'Share of fleet free'}>
              <span style={{ width: `${Math.round(c.bar * 100)}%` }} />
              <span className="ds-ticks"><span>0</span><span>50</span><span>100</span></span>
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}
