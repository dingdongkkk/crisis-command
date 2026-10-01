import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { validateContract, type ContractName } from './contracts'

const examples = resolve(import.meta.dirname, '../../docs/decisions/examples')
const load = (name: string): unknown => {
  const strip = (v: unknown): unknown =>
    Array.isArray(v)
      ? v.map(strip)
      : v && typeof v === 'object'
        ? Object.fromEntries(Object.entries(v).filter(([k]) => k !== '_comment').map(([k, x]) => [k, strip(x)]))
        : v
  return strip(JSON.parse(readFileSync(resolve(examples, name), 'utf8')))
}

interface ApiCase {
  name: string
  response: { status: number; body: unknown }
}

describe('UI mocks validate against the backend-generated schema', () => {
  it.each<[string, ContractName]>([
    ['plan.valid.json', 'Plan'],
    ['world.before.json', 'StateSnapshot'],
    ['policy.valid.json', 'Policy'],
  ])('%s is a valid %s', (file, name) => {
    expect(validateContract(name, load(file))).toEqual({ valid: true, errors: [] })
  })

  it('every example event is a valid EventEnvelope', () => {
    for (const event of load('events.valid.json') as unknown[]) {
      expect(validateContract('EventEnvelope', event).errors).toEqual([])
    }
  })

  it('every problem response is a valid Problem', () => {
    const problems = (load('api.examples.json') as ApiCase[]).filter((c) => c.response.status >= 400)
    expect(problems.length).toBeGreaterThan(5)
    for (const c of problems) expect(validateContract('Problem', c.response.body).errors).toEqual([])
  })

  it('rejects unknown fields and wrong fact values', () => {
    const plan = load('plan.valid.json') as Record<string, unknown>
    expect(validateContract('Plan', { ...plan, dispatched: true }).valid).toBe(false)
    const fact = { key: 'conscious', value: false, source: 'rule_adapter', evidence: [], updated_sim_time_s: 1, confirmed_by_operator: false }
    expect(validateContract('TriageFact', fact).valid).toBe(false)
  })
})

describe('schema bounds reach runtime validation', () => {
  it('rejects negative seconds and out-of-range coordinates', () => {
    const plan = load('plan.valid.json') as { assignments: { eta_s: number }[] }
    const negative = structuredClone(plan)
    negative.assignments = negative.assignments.map((a, i) => (i === 0 ? { ...a, eta_s: -5 } : a))
    expect(validateContract('Plan', negative).valid).toBe(false)
    expect(validateContract('Point', { type: 'Point', coordinates: [12.9, 177.6] }).valid).toBe(false)
    expect(validateContract('Point', { type: 'Point', coordinates: [77.6, 12.9] }).valid).toBe(true)
  })
})
