import type { Incident } from '../contracts'
import { SEVERITY_RANK } from './labels'

/** Active emergency incidents by severity, then oldest first (longest waiting). */
export function sortEmergencies(incidents: Incident[]): Incident[] {
  return incidents
    .filter((i) => i.category === 'emergency' && i.status === 'active')
    .sort(
      (a, b) =>
        (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9) ||
        a.created_sim_time_s - b.created_sim_time_s ||
        a.incident_id.localeCompare(b.incident_id),
    )
}
