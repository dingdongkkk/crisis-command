import type { LiveUpdate } from '../api/types'
import { validateContract } from '../contracts'
import { derivePlanView } from '../state/planView'
import { MOCK_SCENARIOS, MockConsoleApi, snapshotT10 } from './mockApi'

/** Every snapshot a mock emits must be a valid StateSnapshot: mocks may not drift from the contract. */
async function collect(api: MockConsoleApi, run: (api: MockConsoleApi) => Promise<unknown>) {
  const states: unknown[] = []
  const stop = api.connect((u: LiveUpdate) => u.kind === 'state' && states.push(u.state))
  await run(api)
  await new Promise((r) => setTimeout(r, 60))
  stop()
  return states
}

describe('mock backend stays contract-valid', () => {
  it('initial snapshot for every scenario that loads', async () => {
    for (const scenario of MOCK_SCENARIOS.filter((s) => s !== 'loading' && s !== 'error')) {
      const state = await new MockConsoleApi(scenario, 0).loadState()
      expect(validateContract('StateSnapshot', state).errors).toEqual([])
    }
  })

  it('approval and dispatch states', async () => {
    const snapshot = snapshotT10()
    const plan = snapshot.current_proposal
    if (!plan) throw new Error('fixture has a proposal')
    const flags = plan.flags.filter((f) => f.requires_ack).map((f) => f.flag_id)
    const body = { expected_session_id: snapshot.session_id, expected_plan_version: 7, expected_planning_sequence: 58, acknowledged_flag_ids: flags }
    const states = await collect(new MockConsoleApi('demo', 1), (api) => api.approve(plan.plan_id, body, 'k'))
    expect(states.length).toBe(2)
    for (const s of states) expect(validateContract('StateSnapshot', s).errors).toEqual([])
  })

  it('stale approval and override recompute produce valid renumbered plans', async () => {
    const snapshot = snapshotT10()
    const plan = snapshot.current_proposal
    if (!plan) throw new Error('fixture has a proposal')
    const flags = plan.flags.filter((f) => f.requires_ack).map((f) => f.flag_id)
    const stale = await collect(new MockConsoleApi('stale', 1), (api) =>
      api.approve(plan.plan_id, { expected_session_id: 'sess_demo_01', expected_plan_version: 7, expected_planning_sequence: 58, acknowledged_flag_ids: flags }, 'k'),
    )
    const bridged = await collect(new MockConsoleApi('demo', 1), (api) =>
      api.submitOverride({ kind: 'approve_bls_bridge', unit_id: 'unit_B2', bridges_need_id: 'need_0006_als', expected_session_id: 'sess_demo_01', expected_plan_id: 'plan_0007', expected_planning_sequence: 58, reason_text: 'x' }, 'k'),
    )
    for (const s of [...stale, ...bridged]) expect(validateContract('StateSnapshot', s).errors).toEqual([])
  })
})

describe('plan view derivation', () => {
  it('is proposed only while the proposal binds the current planning sequence', () => {
    const snapshot = snapshotT10()
    expect(derivePlanView(snapshot, false).kind).toBe('proposed')
    expect(derivePlanView({ ...snapshot, planning_sequence: 59 }, false).kind).toBe('stale')
    expect(derivePlanView({ ...snapshot, current_proposal: null }, true).kind).toBe('computing')
    expect(derivePlanView({ ...snapshot, current_proposal: null }, false).kind).toBe('dispatched')
    expect(derivePlanView({ ...snapshot, current_proposal: null, approved_plan: null }, false).kind).toBe('no_plan')
  })
})
