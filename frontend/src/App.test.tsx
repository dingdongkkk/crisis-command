import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ApiResult, ConsoleApi, LiveUpdate } from './api/types'
import { App } from './App'
import type { ApproveCommand, StateSnapshot } from './contracts'
import { MockConsoleApi, snapshotT10, type MockScenario } from './mocks/mockApi'

const ACK_COUNT = 5

function setup(scenario: MockScenario = 'demo', options: { tiles?: boolean } = {}) {
  const api = new MockConsoleApi(scenario, 5)
  const user = userEvent.setup()
  render(<App api={api} mapTiles={options.tiles ?? false} />)
  return { api, user }
}

async function ready() {
  await screen.findByText(/PROPOSED v7 — not dispatched/)
  await screen.findByText(/^Live · seq 60/)
}

const approveButton = () => screen.getByRole('button', { name: /^Approve and dispatch \(simulated\)/ })

async function ackAll(user: ReturnType<typeof userEvent.setup>) {
  for (const box of screen.getAllByRole('checkbox', { name: /I understand/ })) await user.click(box)
}

describe('page states', () => {
  it('always states the simulation boundary', async () => {
    setup()
    expect(screen.getByRole('note')).toHaveTextContent('SIMULATION — synthetic data only. No real calls, dispatch or notifications.')
    await ready()
  })

  it('shows a loading state with no commands', () => {
    setup('loading')
    expect(screen.getByText('Loading simulation state…')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Approve/ })).not.toBeInTheDocument()
  })

  it('shows an error state with retry', async () => {
    setup('error')
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load simulation state')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('shows empty states', async () => {
    setup('empty')
    expect(await screen.findByText('No active emergency incidents.')).toBeInTheDocument()
    expect(screen.getByText('No proposal and no approved plan.')).toBeInTheDocument()
    expect(screen.getByText('Select an incident to see its facts.')).toBeInTheDocument()
  })

  it('disables commands when disconnected and shows data age', async () => {
    setup('disconnected')
    expect(await screen.findByText(/Disconnected — data as of seq 60/)).toBeInTheDocument()
    expect(approveButton()).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByRole('button', { name: 'Override…' })).toBeDisabled()
    expect(screen.getByText('Commands are disabled until the console is live.')).toBeInTheDocument()
  })

  it('keeps commands available but visibly degraded when the model is down', async () => {
    setup('degraded')
    expect(await screen.findByText(/Degraded: Language model unavailable — rule intake active/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Override…' })).toBeEnabled()
  })

  it('pauses approval while the world is changing', async () => {
    setup('world_changing')
    expect(await screen.findByText(/World changing — .*Approval paused/)).toBeInTheDocument()
    expect(approveButton()).toHaveAttribute('aria-disabled', 'true')
  })
})

describe('proposed versus approved', () => {
  it('never presents an unapproved plan as dispatched', async () => {
    setup()
    await ready()
    expect(screen.getByText('PROPOSED v7 — not dispatched')).toBeInTheDocument()
    expect(screen.queryByText(/DISPATCHED/)).not.toBeInTheDocument()
    expect(screen.getByText(/Approved plan v6 remains in force/)).toBeInTheDocument()
  })

  it('requires every flag acknowledgement before approval, then approves and dispatches (simulated)', async () => {
    const { api, user } = setup()
    await ready()
    expect(approveButton()).toHaveAttribute('aria-disabled', 'true')
    expect(approveButton()).toHaveAccessibleName(`Approve and dispatch (simulated) — ${ACK_COUNT} flags need acknowledgement`)
    await user.click(approveButton())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await ackAll(user)
    expect(approveButton()).toHaveAttribute('aria-disabled', 'false')
    expect(approveButton()).toHaveAccessibleName('Approve and dispatch (simulated)')

    await user.click(approveButton())
    const dialog = screen.getByRole('dialog', { name: 'Approve plan v7?' })
    expect(dialog).toHaveTextContent('simulated dispatch commands only')
    await user.click(within(dialog).getByRole('button', { name: 'Approve & dispatch (simulated)' }))

    expect(await screen.findByText('APPROVED v7 — dispatch queued (simulated)')).toBeInTheDocument()
    expect(await screen.findByText('DISPATCHED (simulated) v7')).toBeInTheDocument()
    const [request] = api.requests
    const body = request?.body as ApproveCommand
    expect(body).toMatchObject({ expected_session_id: 'sess_demo_01', expected_plan_version: 7, expected_planning_sequence: 58 })
    expect(body.acknowledged_flag_ids).toHaveLength(ACK_COUNT)
  })

  it('handles a stale approval: nothing approved, new version shown, acknowledgements reset', async () => {
    const { user } = setup('stale')
    await ready()
    await ackAll(user)
    await user.click(approveButton())
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Approve & dispatch (simulated)' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Not approved: plan changed (now v8). Review the new plan.')
    expect(await screen.findByText('PROPOSED v8 — not dispatched')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Plan' })).toHaveFocus()
    expect(approveButton()).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getAllByRole('checkbox', { name: /I understand/ }).every((b) => !(b as HTMLInputElement).checked)).toBe(true)
  })

  it('retries a busy server with the same idempotency key', async () => {
    const { api, user } = setup('busy')
    await ready()
    await ackAll(user)
    await user.click(approveButton())
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Approve & dispatch (simulated)' }))
    expect(await screen.findByText('APPROVED v7 — dispatch queued (simulated)')).toBeInTheDocument()
    expect(api.requests.map((r) => r.key)).toHaveLength(2)
    expect(new Set(api.requests.map((r) => r.key)).size).toBe(1)
  })
})

describe('plan diff and explanations', () => {
  it('shows unmet ALS with why-not reasons, bridge candidates and grouped changes', async () => {
    setup()
    await ready()
    expect(screen.getByRole('heading', { name: 'Unmet needs (2)' })).toBeInTheDocument()
    expect(screen.getAllByText(/unit_A1 is on scene at inc_0001 and locked/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/unit_A2 is out of service \(Broken down\)/).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('button', { name: 'Propose BLS bridge…' }).length).toBeGreaterThan(0)
    expect(screen.getByRole('heading', { name: 'New (3)' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Released (1)' })).toBeInTheDocument()
    expect(screen.getByText(/unit_A2: released from inc_0004/)).toBeInTheDocument()
  })
})

describe('overrides', () => {
  it('shows a conflicting pin in words and applies nothing', async () => {
    const { user } = setup()
    await ready()
    await user.click(screen.getByRole('button', { name: 'Override…' }))
    const dialog = screen.getByRole('dialog', { name: 'Override' })
    await user.selectOptions(within(dialog).getByLabelText('Unit'), 'unit_A1')
    await user.selectOptions(within(dialog).getByLabelText('Need'), 'need_0006_als')
    await user.type(within(dialog).getByLabelText(/Reason/), 'Send A1 to the school')
    await user.click(within(dialog).getByRole('button', { name: 'Submit override' }))
    const alert = await within(dialog).findByRole('alert')
    expect(alert).toHaveTextContent('Override rejected — nothing was applied.')
    expect(alert).toHaveTextContent('unit_A1 is locked on its current task.')
    expect(screen.getByText('PROPOSED v7 — not dispatched')).toBeInTheDocument()
  })

  it('proposes a BLS bridge from an unmet need; the result still needs approval', async () => {
    const { api, user } = setup()
    await ready()
    await user.click(screen.getAllByRole('button', { name: 'Propose BLS bridge…' })[0] as HTMLElement)
    const dialog = screen.getByRole('dialog', { name: 'Override' })
    expect(within(dialog).getByLabelText('Kind')).toHaveValue('approve_bls_bridge')
    await user.type(within(dialog).getByLabelText(/Reason/), 'No ALS available')
    await user.click(within(dialog).getByRole('button', { name: 'Submit override' }))
    expect(await screen.findByText(/Override ovr_0002 recorded/)).toBeInTheDocument()
    expect(api.requests.at(-1)?.body).toMatchObject({ kind: 'approve_bls_bridge', expected_plan_id: 'plan_0007', expected_planning_sequence: 58 })
    await user.click(screen.getByRole('button', { name: 'Close' }))
    expect(await screen.findByText('PROPOSED v8 — not dispatched')).toBeInTheDocument()
  })
})

describe('keyboard', () => {
  it('moves through the queue with j/k, opens triage with Enter, focuses Approve with a, opens override with o', async () => {
    const { user } = setup()
    await ready()
    await user.keyboard('j')
    const first = screen.getAllByRole('button', { current: true })[0]
    expect(first).toHaveFocus()
    await user.keyboard('j')
    await user.keyboard('j')
    expect(document.activeElement).toHaveAttribute('data-incident-id', 'inc_0006')
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Triage · inc_0006' })).toHaveFocus())
    await user.keyboard('a')
    await waitFor(() => expect(approveButton()).toHaveFocus())
    await user.keyboard('o')
    expect(screen.getByRole('dialog', { name: 'Override' })).toBeInTheDocument()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('keeps the selected incident across live updates', async () => {
    const { user } = setup()
    await ready()
    await user.click(screen.getByRole('button', { name: /inc_0006/ }))
    await ackAll(user)
    await user.click(approveButton())
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Approve & dispatch (simulated)' }))
    await screen.findByText('DISPATCHED (simulated) v7')
    expect(screen.getByRole('button', { name: /inc_0006/ })).toHaveAttribute('aria-current', 'true')
    expect(screen.getByRole('heading', { name: 'Triage · inc_0006' })).toBeInTheDocument()
  })
})

describe('triage facts', () => {
  it('keeps unknown critical facts visible and labels provisional needs and model coercions', async () => {
    const { user } = setup()
    await ready()
    await user.click(screen.getByRole('button', { name: /inc_0006/ }))
    expect(screen.getByText('With operator — reason: Life threat indicated')).toBeInTheDocument()
    const unknown = screen.getByRole('heading', { name: 'Not established — treated as present for planning' }).parentElement as HTMLElement
    expect(unknown).toHaveTextContent('Conscious: UNKNOWN')
    expect(screen.getByText(/model said NO without evidence/)).toBeInTheDocument()
    expect(screen.getAllByText('PROVISIONAL').length).toBeGreaterThan(0)
  })
})

describe('unrecognised values', () => {
  it('renders unknown enum values as Unrecognised and refuses approval', async () => {
    const snapshot = snapshotT10()
    const proposal = snapshot.current_proposal as NonNullable<StateSnapshot['current_proposal']>
    proposal.flags = proposal.flags.map((f, i) => (i === 0 ? { ...f, severity: 'catastrophic' as never, requires_ack: false } : { ...f, requires_ack: false }))
    const api: ConsoleApi = {
      loadState: async () => snapshot,
      approve: async (): Promise<ApiResult<never>> => { throw new Error('must not be called') },
      submitOverride: async (): Promise<ApiResult<never>> => { throw new Error('unused') },
      connect: (listener: (u: LiveUpdate) => void) => {
        setTimeout(() => listener({ kind: 'connection', status: 'live' }))
        return () => undefined
      },
    }
    render(<App api={api} mapTiles={false} />)
    expect(await screen.findByText('Unrecognised (catastrophic)')).toBeInTheDocument()
    await screen.findByText(/^Live/)
    expect(approveButton()).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByText(/cannot display \(catastrophic\)/)).toBeInTheDocument()
  })
})

describe('layout', () => {
  it('shows OpenStreetMap attribution with tiles enabled', async () => {
    setup('demo', { tiles: true })
    await ready()
    expect(document.querySelector('.leaflet-control-attribution')).toHaveTextContent('OpenStreetMap contributors')
  })

  it('uses tabs and a sticky plan status on narrow screens', async () => {
    const original = window.matchMedia
    window.matchMedia = ((query: string) => ({
      matches: true, media: query, onchange: null,
      addEventListener: () => undefined, removeEventListener: () => undefined,
      addListener: () => undefined, removeListener: () => undefined, dispatchEvent: () => false,
    })) as typeof window.matchMedia
    try {
      const { user } = setup()
      await screen.findByRole('tablist', { name: 'Console sections' })
      expect(screen.getByRole('tab', { name: 'Queue' })).toHaveAttribute('aria-selected', 'true')
      await waitFor(() => expect(screen.getAllByRole('status').some((s) => s.textContent?.includes('PROPOSED v7 — not dispatched'))).toBe(true))
      await user.click(screen.getByRole('button', { name: 'Review plan' }))
      expect(screen.getByRole('tab', { name: 'Plan' })).toHaveAttribute('aria-selected', 'true')
      expect(screen.getByRole('heading', { name: 'Plan' })).toBeInTheDocument()
    } finally {
      window.matchMedia = original
    }
  })
})

// Keep timers from leaking between tests.
afterEach(async () => {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 30))
  })
})
