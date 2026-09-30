import { useEffect, useMemo, useRef, useState, type ReactElement } from 'react'
import type { ConsoleApi } from './api/types'
import { ApproveDialog } from './components/ApproveDialog'
import { ConnectionBanner, SimulationBanner } from './components/Banners'
import { FleetList } from './components/FleetList'
import { IncidentQueue } from './components/IncidentQueue'
import { MapView } from './components/MapView'
import { OverrideDialog, type OverridePrefill } from './components/OverrideDialog'
import { PlanPanel } from './components/PlanPanel'
import { TriagePanel } from './components/TriagePanel'
import { sortEmergencies } from './state/queue'
import { commandsEnabled, useConsole } from './state/useConsole'

export interface AppProps {
  api: ConsoleApi
  /** Disable map tiles (tests, offline demos). Features and attribution still render. */
  mapTiles?: boolean
}

const TABS = ['Queue', 'Map', 'Plan', 'Triage', 'Fleet'] as const
type Tab = (typeof TABS)[number]

function useNarrow(): boolean {
  const query = '(max-width: 899px)'
  const [narrow, setNarrow] = useState(() => typeof window !== 'undefined' && !!window.matchMedia?.(query).matches)
  useEffect(() => {
    const mql = window.matchMedia?.(query)
    if (!mql) return
    const onChange = () => setNarrow(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])
  return narrow
}

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))

export function App({ api, mapTiles = true }: AppProps) {
  const { state, planView, select, ack, approve, submitOverride, clearPlanAction } = useConsole(api)
  const [dialog, setDialog] = useState<null | { kind: 'approve' } | { kind: 'override'; prefill?: OverridePrefill }>(null)
  const [tab, setTab] = useState<Tab>('Queue')
  const narrow = useNarrow()
  const approveRef = useRef<HTMLButtonElement>(null)
  const planHeaderRef = useRef<HTMLHeadingElement>(null)
  const triageRef = useRef<HTMLHeadingElement>(null)
  const { snapshot } = state
  const enabled = commandsEnabled(state)

  const emergencies = useMemo(() => (snapshot ? sortEmergencies(snapshot.incidents) : []), [snapshot])
  const selected = snapshot?.incidents.find((i) => i.incident_id === state.selectedIncidentId) ?? null
  const selectedFacts = snapshot?.triage_facts.find((t) => t.incident_id === state.selectedIncidentId) ?? null
  const plan = planView && 'plan' in planView ? planView.plan : null
  const overridePlan = snapshot?.current_proposal ?? snapshot?.approved_plan ?? null

  // A rejected approval moves focus to the (new) plan header so the operator re-reviews.
  useEffect(() => {
    if (state.planAction.kind === 'rejected') planHeaderRef.current?.focus()
  }, [state.planAction])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (dialog || isTyping(event.target) || event.metaKey || event.ctrlKey || event.altKey) return
      if (event.key === 'j' || event.key === 'k') {
        if (emergencies.length === 0) return
        const index = emergencies.findIndex((i) => i.incident_id === state.selectedIncidentId)
        const next = event.key === 'j' ? Math.min(index + 1, emergencies.length - 1) : Math.max(index - 1, 0)
        const target = emergencies[index === -1 ? 0 : next]
        if (!target) return
        select(target.incident_id)
        document.querySelector<HTMLButtonElement>(`[data-incident-id="${target.incident_id}"]`)?.focus()
        event.preventDefault()
      } else if (event.key === 'Enter' && state.selectedIncidentId && document.activeElement?.hasAttribute('data-incident-id')) {
        if (narrow) setTab('Triage')
        setTimeout(() => triageRef.current?.focus())
      } else if (event.key === 'a') {
        // Focus only: approval always needs an explicit activation and confirmation.
        if (narrow) setTab('Plan')
        setTimeout(() => approveRef.current?.focus())
        event.preventDefault()
      } else if (event.key === 'o' && enabled && overridePlan) {
        setDialog({ kind: 'override' })
        event.preventDefault()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dialog, emergencies, state.selectedIncidentId, select, enabled, overridePlan, narrow])

  const banner = (
    <>
      <SimulationBanner />
      <ConnectionBanner
        status={state.connection}
        detail={state.connectionDetail ?? state.loadError}
        sequence={snapshot?.as_of_sequence ?? null}
        simTimeS={snapshot?.sim_time_s ?? null}
        lastLiveAt={state.lastLiveAt}
      />
      {state.sessionChanged && (
        <p className="notice" role="alert">Simulation was reset. The console now shows the new session.</p>
      )}
    </>
  )

  if (state.load === 'loading') {
    return (
      <>
        {banner}
        <main className="loading" aria-busy="true">
          <h1>Crisis Command</h1>
          <p>Loading simulation state…</p>
          <div className="skeleton" aria-hidden="true" />
        </main>
      </>
    )
  }
  if (state.load === 'error' || !snapshot || !planView) {
    return (
      <>
        {banner}
        <main>
          <h1>Crisis Command</h1>
          <div className="notice notice-error" role="alert">
            <p>Could not load simulation state: {state.loadError ?? 'unknown error'}</p>
            <button type="button" onClick={() => window.location.reload()}>Retry</button>
          </div>
        </main>
      </>
    )
  }

  const panels: Record<Tab, ReactElement> = {
    Queue: <IncidentQueue incidents={snapshot.incidents} proposal={snapshot.current_proposal} selectedId={state.selectedIncidentId} onSelect={select} />,
    Map: <MapView snapshot={snapshot} proposal={snapshot.current_proposal} selectedId={state.selectedIncidentId} onSelect={select} tiles={mapTiles} />,
    Plan: (
      <PlanPanel
        ref={planHeaderRef}
        view={planView}
        action={state.planAction}
        acked={state.acks.flagIds}
        commandsEnabled={enabled}
        onAck={ack}
        onApprove={() => setDialog({ kind: 'approve' })}
        onOverride={(prefill) => setDialog({ kind: 'override', prefill })}
        onDismissNotice={clearPlanAction}
        approveRef={approveRef}
      />
    ),
    Triage: <TriagePanel ref={triageRef} incident={selected} facts={selectedFacts} />,
    Fleet: <FleetList units={snapshot.units} />,
  }

  return (
    <>
      {banner}
      <header className="app-header">
        <h1>Crisis Command</h1>
        <span className="muted">session {snapshot.session_id} · keys: j/k move · Enter open · a focus Approve · o override · Esc close</span>
      </header>
      {narrow ? (
        <>
          <div className="sticky-plan" role="status">
            {planView.kind === 'proposed' ? `PROPOSED v${planView.plan.version} — not dispatched` : planView.kind.replace('_', ' ').toUpperCase()}
            {tab !== 'Plan' && (
              <button type="button" className="link" onClick={() => setTab('Plan')}>Review plan</button>
            )}
          </div>
          <div role="tablist" aria-label="Console sections" className="tabs">
            {TABS.map((t) => (
              <button key={t} role="tab" id={`tab-${t}`} aria-selected={tab === t} aria-controls={`tabpanel-${t}`} onClick={() => setTab(t)} type="button">
                {t}
              </button>
            ))}
          </div>
          <main role="tabpanel" id={`tabpanel-${tab}`} aria-labelledby={`tab-${tab}`} className="narrow-main">
            {panels[tab]}
          </main>
        </>
      ) : (
        <main className="grid">
          <div className="area-queue">{panels.Queue}</div>
          <div className="area-map">{panels.Map}</div>
          <div className="area-plan">{panels.Plan}</div>
          <div className="area-triage">{panels.Triage}</div>
          <div className="area-fleet">{panels.Fleet}</div>
        </main>
      )}
      {dialog?.kind === 'approve' && plan && (
        <ApproveDialog
          plan={plan}
          onCancel={() => setDialog(null)}
          onConfirm={(note) => {
            setDialog(null)
            void approve(plan, note || undefined)
          }}
        />
      )}
      {dialog?.kind === 'override' && overridePlan && (
        <OverrideDialog snapshot={snapshot} plan={overridePlan} prefill={dialog.prefill} onSubmit={submitOverride} onClose={() => setDialog(null)} />
      )}
    </>
  )
}
