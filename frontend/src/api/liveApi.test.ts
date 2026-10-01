import type { StateSnapshot } from '../contracts'
import { snapshotT10 } from '../mocks/mockApi'
import { LiveConsoleApi } from './liveApi'
import type { LiveUpdate } from './types'

/** Scripted stand-in for the server side of `/ws/events`. */
class FakeSocket {
  static OPEN = 1
  static instances: FakeSocket[] = []
  readyState = 0
  sent: unknown[] = []
  onopen: (() => void) | null = null
  onmessage: ((m: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  constructor(readonly url: string) {
    FakeSocket.instances.push(this)
  }
  send(data: string) {
    this.sent.push(JSON.parse(data))
  }
  close() {
    if (this.readyState === 3) return
    this.readyState = 3
    this.onclose?.()
  }
  // server-side helpers
  open() {
    this.readyState = FakeSocket.OPEN
    this.onopen?.()
  }
  push(message: unknown) {
    this.onmessage?.({ data: JSON.stringify(message) })
  }
}

interface ServerState {
  session: string
  sequence: number
  stateCalls: number
  responses: Record<string, { status: number; body: unknown; headers?: Record<string, string> }>
  requests: { method: string; url: string; headers: Record<string, string>; body: unknown }[]
  offline: boolean
}

function server(): { srv: ServerState; fetchImpl: typeof fetch } {
  const srv: ServerState = { session: 'sess_demo_01', sequence: 60, stateCalls: 0, responses: {}, requests: [], offline: false }
  const fetchImpl = (async (url: string, init?: RequestInit) => {
    if (srv.offline) throw new TypeError('Failed to fetch')
    const method = init?.method ?? 'GET'
    srv.requests.push({ method, url, headers: (init?.headers as Record<string, string>) ?? {}, body: init?.body ? JSON.parse(String(init.body)) : undefined })
    if (url.endsWith('/state')) {
      srv.stateCalls += 1
      const snap: StateSnapshot = { ...snapshotT10(), session_id: srv.session, as_of_sequence: srv.sequence }
      return new Response(JSON.stringify(snap), { status: 200 })
    }
    const scripted = Object.entries(srv.responses).find(([pattern]) => url.includes(pattern))?.[1]
    if (!scripted) return new Response('{}', { status: 404 })
    return new Response(JSON.stringify(scripted.body), { status: scripted.status, headers: scripted.headers })
  }) as typeof fetch
  return { srv, fetchImpl }
}

function event(sequence: number, session = 'sess_demo_01', type = 'UnitStatusChanged', planning = true) {
  return { type: 'event', event: { session_id: session, sequence, event_type: type, affects_planning: planning } }
}

async function setup() {
  FakeSocket.instances = []
  const { srv, fetchImpl } = server()
  const api = new LiveConsoleApi({
    baseUrl: '/api',
    wsUrl: 'ws://test/api/ws/events',
    fetchImpl,
    WebSocketImpl: FakeSocket as unknown as typeof WebSocket,
    silenceMs: 30_000,
    refreshDebounceMs: 100,
    backoffMs: [1000, 2000],
  })
  const updates: LiveUpdate[] = []
  await api.loadState()
  const stop = api.connect((u) => updates.push(u))
  const ws = FakeSocket.instances[0]
  if (!ws) throw new Error('client did not open a socket')
  ws.open()
  ws.push({ type: 'hello', session_id: srv.session, head_sequence: srv.sequence, schema_version: '1.0' })
  return { api, srv, ws, updates, stop }
}

const kinds = (updates: LiveUpdate[]) =>
  updates.map((u) => (u.kind === 'connection' ? `connection:${u.status}` : u.kind === 'computing' ? `computing:${u.computing}` : 'state'))

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())

describe('websocket protocol (0005)', () => {
  it('subscribes after the loaded sequence and reports live after catch-up', async () => {
    const { ws, updates, stop } = await setup()
    expect(ws.sent).toEqual([{ type: 'subscribe', session_id: 'sess_demo_01', after_sequence: 60 }])
    ws.push({ type: 'caught_up', head_sequence: 60 })
    expect(kinds(updates)).toEqual(['connection:live'])
    stop()
  })

  it('applies in-order events with one debounced snapshot refresh; duplicates are ignored', async () => {
    const { srv, ws, updates, stop } = await setup()
    const before = srv.stateCalls
    ws.push(event(61))
    ws.push(event(62, undefined, 'PlanProposed', false))
    ws.push(event(61)) // duplicate
    srv.sequence = 62
    await vi.advanceTimersByTimeAsync(150)
    expect(srv.stateCalls - before).toBe(1)
    expect(kinds(updates)).toEqual(['computing:true', 'computing:false', 'state'])
    stop()
  })

  it('resyncs from a snapshot on a sequence gap and resubscribes after it', async () => {
    const { srv, ws, updates, stop } = await setup()
    srv.sequence = 64
    ws.push(event(63)) // expected 61
    await vi.advanceTimersByTimeAsync(0)
    expect(kinds(updates)).toContain('connection:resyncing')
    expect(kinds(updates)).toContain('state')
    expect(ws.sent.at(-1)).toEqual({ type: 'subscribe', session_id: 'sess_demo_01', after_sequence: 64 })
    stop()
  })

  it('treats a new session (demo reset) as a full resync', async () => {
    const { srv, ws, updates, stop } = await setup()
    srv.session = 'sess_demo_02'
    srv.sequence = 1
    ws.push(event(1, 'sess_demo_02', 'SessionStarted'))
    await vi.advanceTimersByTimeAsync(0)
    const last = updates.filter((u) => u.kind === 'state').at(-1)
    expect(last && last.kind === 'state' && last.state.session_id).toBe('sess_demo_02')
    expect(ws.sent.at(-1)).toEqual({ type: 'subscribe', session_id: 'sess_demo_02', after_sequence: 1 })
    stop()
  })

  it('handles snapshot_required from the server', async () => {
    const { srv, ws, updates, stop } = await setup()
    srv.sequence = 70
    ws.push({ type: 'snapshot_required', session_id: 'sess_demo_01' })
    await vi.advanceTimersByTimeAsync(0)
    expect(kinds(updates)).toContain('connection:resyncing')
    expect(ws.sent.at(-1)).toEqual({ type: 'subscribe', session_id: 'sess_demo_01', after_sequence: 70 })
    stop()
  })

  it('goes disconnected after 30 s of silence and reconnects with backoff', async () => {
    const { ws, updates, stop } = await setup()
    await vi.advanceTimersByTimeAsync(29_000)
    ws.push({ type: 'heartbeat', head_sequence: 60 }) // heartbeat resets the watchdog
    await vi.advanceTimersByTimeAsync(29_000)
    expect(kinds(updates)).not.toContain('connection:disconnected')
    await vi.advanceTimersByTimeAsync(1_500) // t = 59.5 s: 30 s after the heartbeat
    expect(kinds(updates)).toContain('connection:disconnected')
    expect(FakeSocket.instances).toHaveLength(1)
    await vi.advanceTimersByTimeAsync(1_000) // first backoff step (1 s) elapses
    expect(FakeSocket.instances).toHaveLength(2)
    stop()
  })
})

describe('commands', () => {
  it('sends the idempotency key and returns typed problems', async () => {
    const { api, srv, stop } = await setup()
    srv.responses['/approve'] = {
      status: 409,
      body: { type: 'x', title: 'Approval rejected', status: 409, code: 'STALE_PLAN', current: { planning_sequence: 61 } },
    }
    const body = { expected_session_id: 'sess_demo_01', expected_plan_version: 7, expected_planning_sequence: 58, acknowledged_flag_ids: [] }
    const result = await api.approve('plan_0007', body, 'key-1')
    expect(result.ok).toBe(false)
    expect(!result.ok && result.problem.code).toBe('STALE_PLAN')
    const sent = srv.requests.at(-1)
    if (!sent) throw new Error('no request recorded')
    expect(sent.headers['Idempotency-Key']).toBe('key-1')
    expect(sent.url).toBe('/api/plans/plan_0007/approve')
    expect(sent.body).toEqual(body)
    stop()
  })

  it('surfaces Retry-After for busy responses and network failures as problems', async () => {
    const { api, srv, stop } = await setup()
    srv.responses['/overrides'] = { status: 503, body: { type: 'x', title: 'Database busy', status: 503, code: 'DATABASE_BUSY' }, headers: { 'Retry-After': '1' } }
    const busy = await api.submitOverride({ kind: 'hold_unit', unit_id: 'unit_B3', expected_session_id: 's', expected_plan_id: 'p', expected_planning_sequence: 1, reason_text: 'x' }, 'k')
    expect(!busy.ok && busy.retryAfterS).toBe(1)
    srv.offline = true
    const down = await api.approve('p', { expected_session_id: 's', expected_plan_version: 1, expected_planning_sequence: 1, acknowledged_flag_ids: [] }, 'k2')
    expect(!down.ok && down.problem.code).toBe('NETWORK_ERROR')
    stop()
  })

  it('returns null route candidates for unknown incidents', async () => {
    const { api, stop } = await setup()
    expect(await api.getRouteCandidates('inc_9999')).toBeNull()
    stop()
  })
})
