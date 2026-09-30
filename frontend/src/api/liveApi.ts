/**
 * Live backend client (CC-09): HTTP commands + the `/ws/events` protocol from decision 0005.
 *
 * The server is authoritative. The browser does not fold events into state (that would
 * duplicate projection logic); each applied event batch triggers a debounced `GET /state`.
 * Sequence discipline still matters: events must arrive as `last + 1` within one session,
 * otherwise the client resyncs from a snapshot and resubscribes after its sequence.
 */
import type {
  ApprovalAccepted,
  ApproveCommand,
  DemoAdvanceResult,
  DemoResetResult,
  HealthResponse,
  OverrideCommand,
  OverrideRecorded,
  Problem,
  ReportAccepted,
  ReportCommand,
  StateSnapshot,
} from '../contracts'
import type { ApiResult, ConsoleApi, DemoStep, LiveUpdate, RouteCandidatesView } from './types'

export interface LiveApiOptions {
  /** HTTP base, e.g. `/api` behind the Vite proxy. */
  baseUrl?: string
  /** WebSocket URL; defaults to `<ws(s)://host><baseUrl>/ws/events`. */
  wsUrl?: string
  fetchImpl?: typeof fetch
  WebSocketImpl?: typeof WebSocket
  /** No message for this long means disconnected (0005: 30 s). */
  silenceMs?: number
  refreshDebounceMs?: number
  backoffMs?: number[]
}

type ServerMessage =
  | { type: 'hello'; session_id: string; head_sequence: number; schema_version: string }
  | { type: 'event'; event: { session_id: string; sequence: number; event_type: string; affects_planning: boolean } }
  | { type: 'heartbeat'; head_sequence: number }
  | { type: 'caught_up'; head_sequence: number }
  | { type: 'snapshot_required'; session_id: string }

const PLAN_OUTCOMES = new Set(['PlanProposed', 'PlanRevalidated', 'PlanFailed', 'PlanApproved'])

function defaultWsUrl(base: string): string {
  const { protocol, host } = window.location
  const path = base.startsWith('http') ? new URL(base).pathname : base
  const origin = base.startsWith('http') ? new URL(base).host : host
  const scheme = base.startsWith('https') || protocol === 'https:' ? 'wss' : 'ws'
  return `${scheme}://${origin}${path.replace(/\/$/, '')}/ws/events`
}

export class LiveConsoleApi implements ConsoleApi {
  private readonly base: string
  private readonly wsUrl: string
  private readonly fetchImpl: typeof fetch
  private readonly WS: typeof WebSocket
  private readonly silenceMs: number
  private readonly debounceMs: number
  private readonly backoff: number[]
  private session: string | null = null
  private lastSequence = 0

  constructor(options: LiveApiOptions = {}) {
    this.base = (options.baseUrl ?? '/api').replace(/\/$/, '')
    this.wsUrl = options.wsUrl ?? defaultWsUrl(this.base)
    this.fetchImpl = options.fetchImpl ?? ((...args) => fetch(...args))
    this.WS = options.WebSocketImpl ?? WebSocket
    this.silenceMs = options.silenceMs ?? 30_000
    this.debounceMs = options.refreshDebounceMs ?? 150
    this.backoff = options.backoffMs ?? [1000, 2000, 4000, 8000]
  }

  // --- HTTP ---------------------------------------------------------------------------

  private async request<T>(method: string, path: string, body?: unknown, key?: string): Promise<ApiResult<T>> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (key) headers['Idempotency-Key'] = key
    let response: Response
    try {
      response = await this.fetchImpl(`${this.base}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      })
    } catch {
      return { ok: false, status: 503, problem: networkProblem() }
    }
    const text = await response.text()
    const data: unknown = text ? JSON.parse(text) : null
    if (response.ok) {
      return { ok: true, status: response.status, body: data as T, replayed: response.headers.get('Idempotent-Replayed') === 'true' }
    }
    const retry = response.headers.get('Retry-After')
    return {
      ok: false,
      status: response.status,
      problem: isProblem(data) ? data : { type: 'about:blank', title: response.statusText || 'Request failed', status: response.status, code: 'HTTP_ERROR' },
      ...(retry ? { retryAfterS: Number(retry) } : {}),
    }
  }

  async loadState(): Promise<StateSnapshot> {
    const result = await this.request<StateSnapshot>('GET', '/state')
    if (!result.ok) throw new Error(`${result.problem.title} (${result.problem.code})`)
    this.session = result.body.session_id
    this.lastSequence = result.body.as_of_sequence
    return result.body
  }

  health(): Promise<ApiResult<HealthResponse>> {
    return this.request<HealthResponse>('GET', '/health')
  }

  approve(planId: string, body: ApproveCommand, key: string): Promise<ApiResult<ApprovalAccepted>> {
    return this.request('POST', `/plans/${encodeURIComponent(planId)}/approve`, body, key)
  }

  submitOverride(body: OverrideCommand, key: string): Promise<ApiResult<OverrideRecorded>> {
    return this.request('POST', '/overrides', body, key)
  }

  async getRouteCandidates(incidentId: string): Promise<RouteCandidatesView | null> {
    const result = await this.request<RouteCandidatesView>('GET', `/routing/candidates?incident_id=${encodeURIComponent(incidentId)}`)
    return result.ok ? result.body : null
  }

  readonly simulation = {
    advance: (step: DemoStep, sessionId: string, key: string) =>
      this.request<DemoAdvanceResult>('POST', '/demo/advance', { expected_session_id: sessionId, to_step: step }, key),
    reset: (sessionId: string, key: string) =>
      this.request<DemoResetResult>('POST', '/demo/reset', { expected_session_id: sessionId, fixture: 'demo-bengaluru-v1', seed: 7 }, key),
  }

  readonly reports = {
    submit: (body: ReportCommand, key: string) => this.request<ReportAccepted>('POST', '/reports', body, key),
  }

  // --- WebSocket ----------------------------------------------------------------------

  connect(listener: (update: LiveUpdate) => void): () => void {
    let socket: WebSocket | null = null
    let closed = false
    let attempt = 0
    let subscribed = false
    let silence: ReturnType<typeof setTimeout> | undefined
    let refresh: ReturnType<typeof setTimeout> | undefined
    let reconnect: ReturnType<typeof setTimeout> | undefined

    const emit = (update: LiveUpdate) => !closed && listener(update)

    const armSilence = () => {
      clearTimeout(silence)
      silence = setTimeout(() => {
        emit({ kind: 'connection', status: 'disconnected', detail: 'No message for 30 s' })
        socket?.close()
      }, this.silenceMs)
    }

    const refreshState = async () => {
      try {
        const state = await this.loadState()
        emit({ kind: 'state', state })
      } catch (error) {
        emit({ kind: 'connection', status: 'error', detail: error instanceof Error ? error.message : 'State unavailable' })
      }
    }

    const scheduleRefresh = () => {
      clearTimeout(refresh)
      refresh = setTimeout(() => void refreshState(), this.debounceMs)
    }

    const subscribe = () => {
      if (socket?.readyState !== this.WS.OPEN || !this.session) return
      subscribed = true
      socket.send(JSON.stringify({ type: 'subscribe', session_id: this.session, after_sequence: this.lastSequence }))
    }

    const resync = async (reason: string) => {
      subscribed = false
      emit({ kind: 'connection', status: 'resyncing', detail: reason })
      await refreshState()
      subscribe()
    }

    const open = () => {
      if (closed) return
      const ws = new this.WS(this.wsUrl)
      socket = ws
      ws.onopen = () => {
        attempt = 0
        armSilence()
      }
      ws.onmessage = (raw: MessageEvent) => {
        armSilence()
        const message = JSON.parse(String(raw.data)) as ServerMessage
        switch (message.type) {
          case 'hello':
            if (this.session && message.session_id !== this.session) {
              void resync('Simulation session changed')
            } else if (!this.session) {
              void refreshState().then(subscribe)
            } else {
              subscribe()
            }
            break
          case 'event': {
            const { event } = message
            if (!subscribed) break
            if (event.session_id !== this.session) {
              void resync('Simulation session changed')
              break
            }
            if (event.sequence <= this.lastSequence) break // duplicate or already in snapshot
            if (event.sequence !== this.lastSequence + 1) {
              void resync(`Sequence gap: expected ${this.lastSequence + 1}, got ${event.sequence}`)
              break
            }
            this.lastSequence = event.sequence
            if (event.affects_planning) emit({ kind: 'computing', computing: true })
            if (PLAN_OUTCOMES.has(event.event_type)) emit({ kind: 'computing', computing: false })
            scheduleRefresh()
            break
          }
          case 'caught_up':
            emit({ kind: 'connection', status: 'live' })
            break
          case 'heartbeat':
            break
          case 'snapshot_required':
            void resync('Server requested a snapshot')
            break
        }
      }
      ws.onclose = () => {
        clearTimeout(silence)
        subscribed = false
        if (closed) return
        emit({ kind: 'connection', status: 'disconnected', detail: 'Connection lost' })
        const delay = this.backoff[Math.min(attempt, this.backoff.length - 1)] ?? 8000
        attempt += 1
        reconnect = setTimeout(open, delay)
      }
      ws.onerror = () => ws.close()
    }

    open()
    return () => {
      closed = true
      clearTimeout(silence)
      clearTimeout(refresh)
      clearTimeout(reconnect)
      socket?.close()
    }
  }
}

function isProblem(value: unknown): value is Problem {
  return typeof value === 'object' && value !== null && 'code' in value && 'status' in value && 'title' in value
}

function networkProblem(): Problem {
  return { type: 'about:blank', title: 'Backend unreachable', status: 503, code: 'NETWORK_ERROR' }
}
