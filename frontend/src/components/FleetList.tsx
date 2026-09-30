import type { Unit } from '../contracts'
import { unitStatusLabel, unitTypeLabel } from '../state/labels'

const STATUS_ICON: Record<string, string> = {
  available: '○',
  en_route: '→',
  on_scene: '■',
  transporting: '⇒',
  at_facility: '⌂',
  returning: '←',
  broken_down: '✕',
  out_of_service: '✕',
  off_duty: '–',
}

export function FleetList({ units }: { units: Unit[] }) {
  return (
    <section className="panel" aria-labelledby="fleet-title">
      <h2 id="fleet-title">Fleet <span className="count">({units.length})</span></h2>
      {units.length === 0 ? (
        <p className="empty">No units in this session.</p>
      ) : (
        <table className="fleet">
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
                <th scope="row">{u.display_name}</th>
                <td>{unitTypeLabel(u.type)}</td>
                <td>
                  <span aria-hidden="true">{STATUS_ICON[u.status] ?? '?'} </span>
                  {unitStatusLabel(u.status)}
                </td>
                <td>{u.current_task ? u.current_task.incident_id : <span className="muted">—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
