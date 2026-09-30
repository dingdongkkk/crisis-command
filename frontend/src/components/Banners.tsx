import { Activity, CloudOff, Keyboard, Moon, RefreshCw, ShieldAlert, Sun, TriangleAlert, WifiOff } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ConnectionStatus } from '../api/types'
import { simClock } from '../state/labels'
import type { Theme } from '../state/theme'

export function SimulationBanner() {
  return (
    <div className="sim-banner" role="note">
      <ShieldAlert size={13} aria-hidden="true" />
      SIMULATION — synthetic data only. No real calls, dispatch or notifications.
    </div>
  )
}

interface ConnectionBannerProps {
  status: ConnectionStatus
  detail: string | null
  sequence: number | null
  simTimeS: number | null
  lastLiveAt: number | null
}

function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!active) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [active])
  return now
}

function age(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

const ICONS = {
  connecting: RefreshCw,
  live: Activity,
  resyncing: RefreshCw,
  disconnected: WifiOff,
  degraded: TriangleAlert,
  world_changing: RefreshCw,
  error: CloudOff,
} as const

export function ConnectionBanner({ status, detail, sequence, simTimeS, lastLiveAt }: ConnectionBannerProps) {
  const now = useNow(status === 'disconnected')
  const seq = sequence == null ? '' : `seq ${sequence}`
  let text: string
  switch (status) {
    case 'connecting':
      text = 'Connecting…'
      break
    case 'live':
      text = `Live · ${seq}${simTimeS == null ? '' : ` · sim ${simClock(simTimeS)}`}`
      break
    case 'resyncing':
      text = 'Resyncing from server…'
      break
    case 'disconnected':
      text = `Disconnected — data as of ${seq}${lastLiveAt ? `, ${age(now - lastLiveAt)} ago` : ''}. Retrying…`
      break
    case 'degraded':
      text = `Degraded: ${detail ?? 'a provider is unavailable'} · ${seq}`
      break
    case 'world_changing':
      text = `World changing — ${detail ?? 'recomputing'}. Approval paused.`
      break
    case 'error':
      text = `Error: ${detail ?? 'state unavailable'}`
      break
  }
  const Icon = ICONS[status]
  return (
    <div className={`conn conn-${status}`} role="status" aria-live="polite">
      <span className="conn-dot" aria-hidden="true">
        <Icon size={13} />
      </span>
      <span>{text}</span>
    </div>
  )
}

interface TopBarProps {
  connection: React.ReactNode
  simTimeS: number | null
  sessionId: string | null
  theme: Theme
  onToggleTheme: () => void
  onShowKeys: () => void
}

export function TopBar({ connection, simTimeS, sessionId, theme, onToggleTheme, onShowKeys }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 16 16" width="16" height="16">
            <path d="M8 1 15 8 8 15 1 8Z" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M8 5 11 8 8 11 5 8Z" fill="currentColor" />
          </svg>
        </span>
        <h1>Crisis Command</h1>
      </div>
      <nav className="crumbs" aria-label="Context">
        <span>Bengaluru</span>
        <span className="crumb-sep" aria-hidden="true">/</span>
        <span className="mono">{sessionId ?? '—'}</span>
        <span className="crumb-sep" aria-hidden="true">/</span>
        <span>Operator console</span>
      </nav>
      <div className="topbar-right">
        {simTimeS != null && (
          <div className="sim-clock" aria-label={`Simulation time ${simClock(simTimeS)}`}>
            <span className="kv-label">SIM TIME</span>
            <span className="mono">{simClock(simTimeS)}</span>
          </div>
        )}
        {connection}
        <span className="topbar-rule" aria-hidden="true" />
        <button type="button" className="icon-btn" onClick={onShowKeys} aria-label="Keyboard shortcuts">
          <Keyboard size={15} />
        </button>
        <button type="button" className="icon-btn" onClick={onToggleTheme} aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}>
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  )
}
