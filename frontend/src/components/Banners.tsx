import { useEffect, useState } from 'react'
import type { ConnectionStatus } from '../api/types'
import { simClock } from '../state/labels'

export function SimulationBanner() {
  return (
    <div className="sim-banner" role="note">
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

const ICON: Record<ConnectionStatus, string> = {
  connecting: '…',
  live: '●',
  resyncing: '↻',
  disconnected: '✕',
  degraded: '!',
  world_changing: '⟳',
  error: '✕',
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
  return (
    <div className={`conn-banner conn-${status}`} role="status" aria-live="polite">
      <span aria-hidden="true">{ICON[status]} </span>
      {text}
    </div>
  )
}
