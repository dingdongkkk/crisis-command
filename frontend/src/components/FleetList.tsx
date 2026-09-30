import type { Unit } from '../contracts'
import { unitStatusLabel, unitTypeLabel } from '../state/labels'
import { UnitTypeIcon } from './icons'

export function FleetList({ units }: { units: Unit[] }) {
  return (
    <section className="rail-section" aria-labelledby="fleet-title">
      <h2 id="fleet-title" className="section-title">Fleet <span className="count">({units.length})</span></h2>
      {units.length === 0 ? (
        <p className="empty">No units in this session.</p>
      ) : (
        <table className="grid-table fleet">
          <thead>
            <tr>
              <th scope="col">Unit</th>
              <th scope="col">Type</th>
              <th scope="col">Status</th>
              <th scope="col">Task</th>
            </tr>
          </thead>
          <tbody>
            {units.map((u) => (
              <tr key={u.unit_id} className={`unit-${u.status}`}>
                <th scope="row" className="mono">
                  <span className="fleet-icon" aria-hidden="true"><UnitTypeIcon type={u.type} size={13} /></span>
                  {u.display_name}
                </th>
                <td>{unitTypeLabel(u.type)}</td>
                <td><span className={`status st-${u.status}`}>{unitStatusLabel(u.status)}</span></td>
                <td className="mono muted">{u.current_task ? u.current_task.incident_id : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
