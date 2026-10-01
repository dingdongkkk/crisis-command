import type { StateSnapshot } from '../contracts'
import { Activity, TriangleAlert, Truck, Wrench, CircleAlert, MapPin } from 'lucide-react'

const metricIcons = [Activity, TriangleAlert, Truck, Wrench, CircleAlert, MapPin]

/** Counts of server-reported state only; the browser does not recompute any policy. */
export function KpiStrip({ snapshot }: { snapshot: StateSnapshot }) {
  const active = snapshot.incidents.filter((i) => i.category === 'emergency' && i.status === 'active')
  const critical = active.filter((i) => i.severity === 'critical').length
  const available = snapshot.units.filter((u) => u.status === 'available' || u.status === 'returning').length
  const plan = snapshot.current_proposal ?? snapshot.approved_plan
  const unmet = plan?.unmet_needs.reduce((n, u) => n + u.quantity_unmet, 0) ?? 0
  const uncovered = plan?.coverage.filter((c) => c.status !== 'covered').length ?? 0
  const outOfService = snapshot.units.filter((u) => ['broken_down', 'out_of_service', 'off_duty'].includes(u.status)).length
  const activeAll = snapshot.incidents.filter((i) => i.status === 'active').length
  const coverageTotal = plan?.coverage.length ?? 0
  const cells = [
    { label: 'Emergencies', value: String(active.length), detail: 'active now', meter: activeAll ? active.length / activeAll : 0, tone: '' },
    { label: 'Critical', value: String(critical), detail: `of ${active.length} active`, meter: active.length ? critical / active.length : 0, tone: critical > 0 ? 'danger' : '' },
    { label: 'Units free', value: `${available}/${snapshot.units.length}`, detail: 'ready or returning', meter: snapshot.units.length ? available / snapshot.units.length : 0, tone: available === 0 ? 'warning' : '' },
    { label: 'Out of service', value: String(outOfService), detail: `of ${snapshot.units.length} units`, meter: snapshot.units.length ? outOfService / snapshot.units.length : 0, tone: outOfService > 0 ? 'danger' : '' },
    { label: 'Unmet needs', value: String(unmet), detail: 'resource requests', meter: unmet > 0 ? 1 : 0, tone: unmet > 0 ? 'danger' : 'success' },
    { label: 'Zones uncovered', value: String(uncovered), detail: `of ${coverageTotal} zones`, meter: coverageTotal ? uncovered / coverageTotal : 0, tone: uncovered > 0 ? 'warning' : 'success' },
  ]
  return (
    <ul className="statbar" aria-label="Situation summary">
      {cells.map((c, index) => {
        const Icon = metricIcons[index]
        return (
        <li key={c.label} className={`stat${c.tone ? ` stat-${c.tone}` : ''}`}>
          {Icon && <Icon className="stat-icon" size={15} aria-hidden="true" />}
          <span className="kv-label">{c.label}</span>
          <span className="stat-value mono">{c.value}</span>
          <span className="stat-detail">{c.detail}</span>
          <span className="stat-meter" aria-hidden="true"><i style={{ width: `${Math.round(c.meter * 100)}%` }} /></span>
        </li>
        )
      })}
    </ul>
  )
}
