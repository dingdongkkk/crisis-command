import { DEMO_STEPS, type DemoStep } from '../api/types'
import type { StateSnapshot } from '../contracts'

// Synthetic locations for simulated calls (approximate public places; fictional incidents).
export const DEMO_PLACES: { label: string; coordinates: [number, number] }[] = [
  { label: 'Indiranagar', coordinates: [77.6408, 12.9784] },
  { label: 'Silk Board junction', coordinates: [77.6229, 12.9177] },
  { label: 'HSR Layout', coordinates: [77.6387, 12.9116] },
  { label: 'Bellandur (ORR)', coordinates: [77.6784, 12.9304] },
  { label: 'Jayanagar', coordinates: [77.5838, 12.93] },
  { label: 'MG Road', coordinates: [77.607, 12.975] },
  { label: 'Koramangala', coordinates: [77.6245, 12.9352] },
  { label: 'Hebbal', coordinates: [77.592, 13.0358] },
]

/** Last applied scripted step, derived from simulation time (steps apply strictly in order). */
export function currentStep(snapshot: StateSnapshot): DemoStep | null {
  const hasScenario = snapshot.incidents.length > 0 || snapshot.sim_time_s > 0
  if (!hasScenario) return null
  return [...DEMO_STEPS].reverse().find((s) => s.simTimeS <= snapshot.sim_time_s)?.step ?? null
}

