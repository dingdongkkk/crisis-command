import { useState } from 'react'
import { App } from '../App'
import type { ConsoleApi } from '../api/types'
import { DemoTour } from './DemoTour'

const TOUR_KEY = 'crisis-command-demo-tour-seen-v1'

interface ConsoleRootProps {
  api: ConsoleApi
  mapTiles: boolean
  tourMode: string | null
}

function tourStartsOpen(mode: string | null): boolean {
  if (mode === 'show') return true
  if (mode === 'skip') return false
  try {
    return sessionStorage.getItem(TOUR_KEY) !== 'yes'
  } catch {
    return true
  }
}

export function ConsoleRoot({ api, mapTiles, tourMode }: ConsoleRootProps) {
  const [tourOpen, setTourOpen] = useState(() => tourStartsOpen(tourMode))
  const finishTour = () => {
    try {
      sessionStorage.setItem(TOUR_KEY, 'yes')
    } catch {
      // The guide still closes when browser storage is unavailable.
    }
    setTourOpen(false)
  }

  return (
    <>
      <div className={`tour-shell${tourOpen ? ' tour-shell-hidden' : ''}`} aria-hidden={tourOpen || undefined}>
        <App api={api} mapTiles={mapTiles} onShowTour={() => setTourOpen(true)} />
      </div>
      {tourOpen && <DemoTour onFinish={finishTour} />}
    </>
  )
}
