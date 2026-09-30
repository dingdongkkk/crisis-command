import { snapshotT10 } from '../mocks/mockApi'
import { flagSubject, kindLabel } from './labels'

describe('flagSubject', () => {
  const snapshot = snapshotT10()
  const incident = snapshot.incidents[0]
  if (!incident) throw new Error('fixture has no incidents')
  const need = incident.needs[0]
  const base = {
    flag_id: 'f1', code: 'ALS_UNMET', severity: 'critical', requires_ack: true, message: 'ALS UNMET',
    incident_id: null, need_id: null, zone_id: null, resource_type: null, since_sim_time_s: null, override_id: null,
  } as const

  it('names the incident and need a bare flag code refers to', () => {
    const text = flagSubject({ ...base, incident_id: incident.incident_id, need_id: need?.need_id ?? null }, snapshot.incidents)
    expect(text).toContain(kindLabel(incident.kind))
    expect(text).toContain(incident.incident_id)
  })

  it('names the reserve zone and resource for coverage flags', () => {
    expect(flagSubject({ ...base, code: 'RESERVE_UNCOVERED', zone_id: 'zone_north', resource_type: 'bls' }, [])).toBe('BLS reserve · north zone')
  })

  it('keeps unknown incidents visible by id and returns null for global flags', () => {
    expect(flagSubject({ ...base, incident_id: 'incident_404' }, [])).toBe('incident_404')
    expect(flagSubject(base, [])).toBeNull()
  })
})
