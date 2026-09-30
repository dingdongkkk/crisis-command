/**
 * Human-readable text for contract enums and reason codes. Status is always text
 * (plus icon), never colour alone. Unknown values render as "Unrecognised (...)"
 * and are reported so the UI can refuse to approve what it cannot display (0001).
 */
import type { Incident, Plan, ReasonFact } from '../contracts'

const SEVERITY: Record<string, string> = { critical: 'CRITICAL', high: 'HIGH', medium: 'MEDIUM', low: 'LOW' }
const SEVERITY_ICON: Record<string, string> = { critical: '▲▲', high: '▲', medium: '◆', low: '●' }
const UNIT_STATUS: Record<string, string> = {
  available: 'Available',
  en_route: 'En route',
  on_scene: 'On scene',
  transporting: 'Transporting',
  at_facility: 'At facility',
  returning: 'Returning',
  broken_down: 'Broken down',
  out_of_service: 'Out of service',
  off_duty: 'Off duty',
}
const UNIT_TYPE: Record<string, string> = { als: 'ALS', bls: 'BLS', fire: 'Fire', boat: 'Boat', tow: 'Tow' }
const NEED_TYPE: Record<string, string> = {
  als: 'ALS',
  bls: 'BLS',
  fire: 'Fire',
  water_rescue: 'Water rescue',
  tow: 'Tow',
  shelter_places: 'Shelter places',
}
const CATEGORY: Record<string, string> = {
  emergency: 'Emergency',
  non_emergency_assist: 'Non-emergency assistance',
  information_request: 'Information request',
}
const FACT_VALUE: Record<string, string> = { yes: 'YES', no: 'NO', unknown: 'UNKNOWN' }
const FACT_SOURCE: Record<string, string> = {
  caller_structured: 'Caller (structured answer)',
  rule_adapter: 'Rules',
  model_adapter: 'Language model',
  operator: 'Operator',
  medical_profile: 'Medical profile',
}
const FLAG_SEVERITY: Record<string, string> = { critical: 'CRITICAL', warning: 'WARNING', info: 'INFO' }
const LOCK: Record<string, string> = { on_scene: 'on scene', transporting: 'transporting', near_arrival: 'arriving (≤120 s)' }
const ESCALATION: Record<string, string> = {
  LIFE_THREAT_INDICATED: 'Life threat indicated',
  CALLER_REQUESTED_HUMAN: 'Caller asked for a person',
  CRITICAL_UNCERTAINTY: 'Critical facts still unknown',
  CONFLICTING_FACTS: 'Conflicting facts',
  MODEL_UNAVAILABLE_CRITICAL_TEXT: 'Model unavailable with critical wording',
}
const FACT_NAME: Record<string, string> = {
  conscious: 'Conscious',
  breathing_normally: 'Breathing normally',
  chest_pain: 'Chest pain',
  severe_bleeding: 'Severe bleeding',
  trapped: 'Trapped',
  fire_or_smoke: 'Fire or smoke',
  gas_smell: 'Gas smell',
  water_rising: 'Water rising',
  people_count: 'People involved',
  caller_in_danger: 'Caller in danger',
}

export function unrecognised(value: string): string {
  return `Unrecognised (${value})`
}

function lookup(table: Record<string, string>, value: string | null | undefined): string {
  if (value == null) return '—'
  return table[value] ?? unrecognised(value)
}

export const isKnown = (table: 'severity' | 'flagSeverity' | 'unitStatus', value: string): boolean =>
  value in { severity: SEVERITY, flagSeverity: FLAG_SEVERITY, unitStatus: UNIT_STATUS }[table]

export const severityLabel = (v: string) => lookup(SEVERITY, v)
export const severityIcon = (v: string) => SEVERITY_ICON[v] ?? '?'
export const unitStatusLabel = (v: string) => lookup(UNIT_STATUS, v)
export const unitTypeLabel = (v: string) => lookup(UNIT_TYPE, v)
export const needTypeLabel = (v: string) => lookup(NEED_TYPE, v)
export const categoryLabel = (v: string) => lookup(CATEGORY, v)
export const factValueLabel = (v: string | null | undefined) => lookup(FACT_VALUE, v)
export const factSourceLabel = (v: string) => lookup(FACT_SOURCE, v)
export const flagSeverityLabel = (v: string) => lookup(FLAG_SEVERITY, v)
export const lockLabel = (v: string | null | undefined) => (v ? lookup(LOCK, v) : '')
export const escalationLabel = (v: string) => ESCALATION[v] ?? v
export const factName = (v: string) => FACT_NAME[v] ?? v.replaceAll('_', ' ')

export const SEVERITY_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }

export function formatSeconds(s: number | null | undefined): string {
  if (s == null) return '—'
  const m = Math.floor(s / 60)
  const r = s % 60
  return m > 0 ? `${m} min ${r.toString().padStart(2, '0')} s` : `${r} s`
}

export function simClock(s: number): string {
  const m = Math.floor(s / 60)
  return `T+${m}:${(s % 60).toString().padStart(2, '0')}`
}

const param = (r: ReasonFact, key: string): string => {
  const value = r.params?.[key]
  return value == null ? '?' : Array.isArray(value) ? value.join(', ') : String(value)
}

/** Explanations are restatements of server reason facts only (0003); no invented numbers. */
export function reasonText(r: ReasonFact): string {
  switch (r.code) {
    case 'UNIT_LOCKED':
      return `${param(r, 'unit_id')} is locked (${lockLabel(param(r, 'lock'))})`
    case 'NEAREST_ELIGIBLE':
      return `${param(r, 'unit_id')} is the nearest eligible unit (${formatSeconds(Number(param(r, 'eta_s')))})`
    case 'ONLY_ELIGIBLE_REMAINING':
      return `${param(r, 'unit_id')} is the only eligible unit left`
    case 'UNIT_UNAVAILABLE':
      return `Unit unavailable (${unitStatusLabel(param(r, 'status'))})`
    case 'ALS_LOCKED_ON_SCENE':
      return `${param(r, 'unit_id')} is on scene at ${param(r, 'incident_id')} and locked`
    case 'ALS_OUT_OF_SERVICE':
      return `${param(r, 'unit_id')} is out of service (${unitStatusLabel(param(r, 'status'))})`
    case 'NO_ALS_AVAILABLE':
      return 'No ALS unit is available'
    case 'NO_ELIGIBLE_CAPACITY':
      return 'No eligible unit is free'
    case 'NO_REACHABLE_UNIT':
      return `No eligible unit can reach it by road (${param(r, 'eligible_units')} eligible, none with a usable route)`
    case 'WATER_ACCESS_NOT_MODELLED':
      return 'Water access is not modelled — boat routes cannot be verified, so no ETA is given'
    case 'ALS_UNREACHABLE':
    case 'ROUTE_UNAVAILABLE':
      return `${param(r, 'unit_id')} has no usable route (flood version ${param(r, 'flood_version')})`
    case 'TYPE_INELIGIBLE':
      return `${param(r, 'unit_id')} is not an eligible type`
    case 'KEPT_FOR_RESERVE':
      return `Kept to cover ${param(r, 'zone_id')}`
    case 'CAPACITY_EXCEEDED':
      return `${param(r, 'facility_id')} has no capacity left`
    case 'OVERRIDE_PIN':
      return `Operator override ${param(r, 'override_id')}`
    case 'SEVERITY_FROM_UNKNOWN':
      return `Assumed from unknown facts: ${param(r, 'facts')}`
    case 'TRAPPED_PERSONS':
      return 'People reported trapped'
    default:
      return `${r.code.replaceAll('_', ' ').toLowerCase()}${Object.keys(r.params ?? {}).length ? ` (${JSON.stringify(r.params)})` : ''}`
  }
}

const CONFLICT: Record<string, string> = {
  UNIT_NOT_AVAILABLE: 'is not available',
  UNIT_LOCKED: 'is locked on its current task',
  TYPE_INELIGIBLE: 'is not an eligible type for that need (use a BLS bridge for ALS shortages)',
  ROUTE_UNAVAILABLE: 'has no usable route',
  CAPACITY_EXCEEDED: 'would exceed capacity',
  DUPLICATE_UNIT_PIN: 'already has an active pin, bridge or hold',
  CONTRADICTS_OVERRIDE: 'contradicts another active override',
}

export function conflictText(c: { code: string; unit_id?: string | null; detail: string }): string {
  const who = c.unit_id ?? 'This override'
  const what = CONFLICT[c.code] ?? c.code.replaceAll('_', ' ').toLowerCase()
  return `${who} ${what}. ${c.detail}`
}

/** Incident kind as a title, e.g. `cardiac_chest_pain` → "Cardiac chest pain". */
export function kindLabel(kind: string): string {
  const text = kind.replaceAll('_', ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/**
 * What a plan flag refers to. The server's `message` is a bare code ("ALS UNMET"), so a
 * list of acknowledgements would otherwise be indistinguishable; the operator must know
 * which incident or zone each one covers before accepting it.
 */
export function flagSubject(flag: Plan['flags'][number], incidents: Incident[]): string | null {
  const parts: string[] = []
  if (flag.incident_id) {
    const incident = incidents.find((i) => i.incident_id === flag.incident_id)
    const need = incident?.needs.find((n) => n.need_id === flag.need_id)
    if (need) parts.push(`${needTypeLabel(need.type)} need`)
    parts.push(incident ? `${kindLabel(incident.kind)} (${flag.incident_id})` : flag.incident_id)
  }
  if (flag.zone_id) {
    parts.push(`${flag.resource_type ? `${needTypeLabel(flag.resource_type)} reserve · ` : ''}${flag.zone_id.replace(/^zone_/, '')} zone`)
  }
  if (flag.override_id) parts.push(`override ${flag.override_id}`)
  return parts.length > 0 ? parts.join(' · ') : null
}

/** English text of the intake's targeted questions (backend `app/intake/questions.py`). */
const QUESTION: Record<string, string> = {
  conscious: 'Is the person conscious and responding to you?',
  breathing_normally: 'Is the person breathing normally?',
  chest_pain: 'Is there chest pain?',
  severe_bleeding: 'Is anyone bleeding heavily?',
  trapped: 'Is anyone trapped or unable to get out?',
  fire_or_smoke: 'Is there any fire or smoke?',
  gas_smell: 'Can you smell gas?',
  water_rising: 'Is the water rising?',
  caller_in_danger: 'Are you in danger where you are right now?',
  people_count: 'How many people are affected?',
}
export const questionText = (key: string) => QUESTION[key] ?? `${factName(key)}?`

const DEGRADED: Record<string, string> = {
  MODEL_UNAVAILABLE: 'Model adapter unavailable — intake is rules-only; critical uncertainty escalates to an operator.',
  ROUTING_DEGRADED: 'Routing provider degraded — plans use fixture road routes; unreachable routes carry no ETA.',
}
export const degradedText = (code: string) => DEGRADED[code] ?? `Degraded: ${code}`
