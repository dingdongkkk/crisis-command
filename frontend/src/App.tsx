import { PhoneIncoming, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactElement } from 'react'
import type { ConsoleApi, RouteCandidatesView } from './api/types'
import { ApproveDialog } from './components/ApproveDialog'
import { Dialog } from './components/Dialog'
import { ConnectionBanner, SimulationBanner, TopBar } from './components/Banners'
import { FleetList } from './components/FleetList'
import { IncidentQueue } from './components/IncidentQueue'
import { KeyboardHelp } from './components/KeyboardHelp'
import { KpiStrip } from './components/KpiStrip'
import { MapView } from './components/MapView'
import { OverrideDialog, type OverridePrefill } from './components/OverrideDialog'
import { PlanPanel } from './components/PlanPanel'
import { ReportDialog } from './components/ReportDialog'
import { ScenarioControls } from './components/ScenarioControls'
import { ReinforcementsPanel } from './components/ReinforcementsPanel'
import { Timeline } from './components/Timeline'
import { TriagePanel } from './components/TriagePanel'
import { sortEmergencies } from './state/queue'
import { useTheme } from './state/theme'
import { commandsEnabled, useConsole } from './state/useConsole'

export interface AppProps {
  api: ConsoleApi
  /** Vector base map on/off (tests, offline demos). Map features always render. */
  mapTiles?: boolean
}

const TABS = ['Queue', 'Map', 'Plan', 'Triage', 'Fleet'] as const
type Tab = (typeof TABS)[number]
type DialogState =
  | null
  /** Bound to the version the operator opened, so a newer proposal can never inherit the confirmation. */
  | { kind: 'approve'; planId: string; version: number }
  | { kind: 'override'; prefill?: OverridePrefill }
  | { kind: 'keys' }
  | { kind: 'report' }

function useNarrow(): boolean {
  const query = '(max-width: 1099px)'
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

type RoutesState = { status: 'idle' | 'loading' | 'error' } | { status: 'ready'; data: RouteCandidatesView }

export function App({ api, mapTiles = true }: AppProps) {
  const { state, planView, select, ack, approve, submitOverride, clearPlanAction } = useConsole(api)
  const [dialog, setDialog] = useState<DialogState>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('Queue')
  const [leftTab, setLeftTab] = useState<'incidents' | 'fleet'>('incidents')
  const [theme, toggleTheme] = useTheme()
  const narrow = useNarrow()
  const approveRef = useRef<HTMLButtonElement>(null)
  const planHeaderRef = useRef<HTMLHeadingElement>(null)
  const triageRef = useRef<HTMLHeadingElement>(null)
  const { snapshot } = state
  const enabled = commandsEnabled(state)

  // Road-router candidates for the selected incident (informational; never changes the plan).
  // Loading/idle are derived from the selection; state is only set when a result arrives.
  const selectedIncidentId = state.selectedIncidentId
  const [routeResult, setRouteResult] = useState<{ incidentId: string; data: RouteCandidatesView | null } | null>(null)
  const [focus, setFocus] = useState<{ incidentId: string; unitId: string | null } | null>(null)
  useEffect(() => {
    if (!selectedIncidentId) return
    let cancelled = false
    api
      .getRouteCandidates(selectedIncidentId)
      .then((data) => !cancelled && setRouteResult({ incidentId: selectedIncidentId, data }))
      .catch(() => !cancelled && setRouteResult({ incidentId: selectedIncidentId, data: null }))
    return () => {
      cancelled = true
    }
  }, [api, selectedIncidentId])
  const routes: RoutesState = useMemo(
    () =>
      !selectedIncidentId
        ? { status: 'idle' }
        : routeResult?.incidentId !== selectedIncidentId
          ? { status: 'loading' }
          : routeResult.data
            ? { status: 'ready', data: routeResult.data }
            : { status: 'error' },
    [selectedIncidentId, routeResult],
  )
  const defaultFocus =
    routes.status === 'ready'
      ? (routes.data.candidates.find(
          (c) => c.route.route_status === 'ok' && !['broken_down', 'out_of_service', 'off_duty'].includes(c.unit_status),
        )?.unit_id ?? null)
      : null
  const focusedUnitId = focus && focus.incidentId === selectedIncidentId ? focus.unitId : defaultFocus
  const setFocusedUnitId = (unitId: string | null) => selectedIncidentId && setFocus({ incidentId: selectedIncidentId, unitId })
  const candidateRoutes = useMemo(
    () => (routes.status === 'ready' ? routes.data.candidates.map((c) => ({ unitId: c.unit_id, route: c.route })) : []),
    [routes],
  )

  const emergencies = useMemo(() => (snapshot ? sortEmergencies(snapshot.incidents) : []), [snapshot])
  const selected = snapshot?.incidents.find((i) => i.incident_id === state.selectedIncidentId) ?? null
  const selectedFacts = snapshot?.triage_facts.find((t) => t.incident_id === state.selectedIncidentId) ?? null
  const plan = planView && 'plan' in planView ? planView.plan : null
  const overridePlan = snapshot?.current_proposal ?? snapshot?.approved_plan ?? null

  // A rejected approval moves focus to the (new) plan header so the operator re-reviews.
  useEffect(() => {
    if (state.planAction.kind === 'rejected') planHeaderRef.current?.focus()
  }, [state.planAction])

  // A new plan state (proposed → approved → dispatched, or a new version) scrolls the plan
  // rail back to its status so the operator sees what changed.
  const planKey = planView ? `${planView.kind}:${'plan' in planView ? planView.plan.plan_id : ''}` : ''
  useEffect(() => {
    document.querySelector('.rail-right')?.scrollTo?.({ top: 0, behavior: 'smooth' })
  }, [planKey])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (dialog || isTyping(event.target) || event.metaKey || event.ctrlKey || event.altKey) return
      if (event.key === 'j' || event.key === 'k') {
        if (emergencies.length === 0) return
        if (!narrow) setLeftTab('incidents')
        const index = emergencies.findIndex((i) => i.incident_id === state.selectedIncidentId)
        const next = event.key === 'j' ? Math.min(index + 1, emergencies.length - 1) : Math.max(index - 1, 0)
        const target = emergencies[index === -1 ? 0 : next]
        if (!target) return
        select(target.incident_id)
        setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-incident-id="${target.incident_id}"]`)?.focus())
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
      } else if (event.key === '?') {
        setDialog({ kind: 'keys' })
        event.preventDefault()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dialog, emergencies, state.selectedIncidentId, select, enabled, overridePlan, narrow])

  const connection = (
    <ConnectionBanner
      status={state.connection}
      detail={state.connectionDetail ?? state.loadError}
      sequence={snapshot?.as_of_sequence ?? null}
      simTimeS={snapshot?.sim_time_s ?? null}
      lastLiveAt={state.lastLiveAt}
    />
  )
  const chrome = (
    <>
      <SimulationBanner />
      <TopBar
        controls={
          snapshot && (api.simulation || api.reports) ? (
            <>
              {api.simulation && (
                <ScenarioControls api={api.simulation} snapshot={snapshot} disabled={!enabled} onNotice={setNotice} />
              )}
              {api.reports && (
                <button type="button" className="scenario-btn" disabled={!enabled} onClick={() => setDialog({ kind: 'report' })}>
                  <PhoneIncoming size={13} aria-hidden="true" /> Simulated call
                </button>
              )}
            </>
          ) : null
        }
        connection={connection}
        simTimeS={snapshot?.sim_time_s ?? null}
        sessionId={snapshot?.session_id ?? null}
        theme={theme}
        onToggleTheme={toggleTheme}
        onShowKeys={() => setDialog({ kind: 'keys' })}
      />
      {state.sessionChanged && (
        <p className="notice notice-strip" role="alert">Simulation was reset. The console now shows the new session.</p>
      )}
      {dialog?.kind === 'keys' && <KeyboardHelp onClose={() => setDialog(null)} />}
      {notice && (
        <p className="notice notice-error notice-strip" role="alert">
          {notice}{' '}
          <button type="button" className="link" onClick={() => setNotice(null)}>Dismiss</button>
        </p>
      )}
      {dialog?.kind === 'report' && snapshot && api.reports && (
        <ReportDialog
          api={api.reports}
          snapshot={snapshot}
          onClose={() => setDialog(null)}
          onCreated={(result) => {
            if (result.incident_id) select(result.incident_id)
          }}
        />
      )}
    </>
  )

  if (state.load === 'loading') {
    return (
      <div className="app">
        {chrome}
        <main className="state-page" aria-busy="true">
          <div className="spinner" aria-hidden="true" />
          <p>Loading simulation state…</p>
        </main>
      </div>
    )
  }
  if (state.load === 'error' || !snapshot || !planView) {
    return (
      <div className="app">
        {chrome}
        <main className="state-page">
          <div className="notice notice-error state-card" role="alert">
            <p>Could not load simulation state: {state.loadError ?? 'unknown error'}</p>
            <button type="button" className="primary" onClick={() => window.location.reload()}>Retry</button>
          </div>
        </main>
      </div>
    )
  }

  const queue = <IncidentQueue incidents={snapshot.incidents} proposal={snapshot.current_proposal ?? snapshot.approved_plan} selectedId={state.selectedIncidentId} onSelect={select} />
  const fleet = <FleetList units={snapshot.units} />
  const map = <MapView snapshot={snapshot} proposal={snapshot.current_proposal} candidates={candidateRoutes} focusedUnitId={focusedUnitId} selectedId={state.selectedIncidentId} onSelect={select} theme={theme} tiles={mapTiles} />
  const triage = <TriagePanel ref={triageRef} incident={selected} facts={selectedFacts} />
  const reinforcements = (
    <ReinforcementsPanel state={routes} focusedUnitId={focusedUnitId} onFocus={setFocusedUnitId} snapshotSequence={snapshot.as_of_sequence} />
  )
  const planPanel = (
    <PlanPanel
      ref={planHeaderRef}
      view={planView}
      incidents={snapshot.incidents}
      action={state.planAction}
      acked={state.acks.flagIds}
      commandsEnabled={enabled}
      onAck={ack}
      onApprove={() => plan && setDialog({ kind: 'approve', planId: plan.plan_id, version: plan.version })}
      onOverride={(prefill) => setDialog({ kind: 'override', prefill })}
      onDismissNotice={clearPlanAction}
      approveRef={approveRef}
    />
  )

  const dialogs = (
    <>
      {dialog?.kind === 'approve' && !(plan && planView?.kind === 'proposed' && plan.plan_id === dialog.planId && plan.version === dialog.version) && (
        <Dialog title="Plan changed — nothing approved" onClose={() => setDialog(null)}>
          <p role="alert">
            Plan v{dialog.version} changed while you were reviewing it
            {plan && plan.version !== dialog.version ? ` (now v${plan.version})` : ''}. Nothing was approved. Review the current plan and its flags.
          </p>
          <div className="dialog-actions">
            <button type="button" className="primary" onClick={() => setDialog(null)}>Review current plan</button>
          </div>
        </Dialog>
      )}
      {dialog?.kind === 'approve' && plan && planView?.kind === 'proposed' && plan.plan_id === dialog.planId && plan.version === dialog.version && (
        <ApproveDialog
          plan={plan}
          incidents={snapshot.incidents}
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

  if (narrow) {
    const panels: Record<Tab, ReactElement> = {
      Queue: queue,
      Map: (
        <div className="narrow-map">
          <KpiStrip snapshot={snapshot} />
          {map}
        </div>
      ),
      Plan: planPanel,
      Triage: (
        <>
          {triage}
          {selected && reinforcements}
        </>
      ),
      Fleet: fleet,
    }
    return (
      <div className="app app-narrow">
        {chrome}
        <div className="sticky-plan" role="status">
          <span>{planView.kind === 'proposed' ? `PROPOSED v${planView.plan.version} — not dispatched` : planView.kind.replace('_', ' ').toUpperCase()}</span>
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
        {dialogs}
      </div>
    )
  }

  return (
    <div className="app">
      {chrome}
      <main className="console">
        <aside className="rail rail-left" aria-label="Incidents and fleet">
          <div className="rail-tabs" aria-label="Left panel">
            <button type="button" aria-pressed={leftTab === 'incidents'} onClick={() => setLeftTab('incidents')}>
              Incidents <span className="seg-count mono">{emergencies.length}</span>
            </button>
            <button type="button" aria-pressed={leftTab === 'fleet'} onClick={() => setLeftTab('fleet')}>
              Fleet <span className="seg-count mono">{snapshot.units.length}</span>
            </button>
          </div>
          <div className="rail-scroll">{leftTab === 'incidents' ? queue : fleet}</div>
        </aside>
        <section className="stage" aria-label="Situation">
          <KpiStrip snapshot={snapshot} />
          <div className="stage-map">{map}</div>
          <Timeline incidents={snapshot.incidents} simTimeS={snapshot.sim_time_s} selectedId={state.selectedIncidentId} onSelect={select} />
          <div className={`detail-dock${selected ? ' open' : ''}`}>
            {selected && (
              <button type="button" className="icon-btn dock-close" aria-label="Close triage" onClick={() => select(null)}>
                <X size={14} />
              </button>
            )}
            <div className="dock-body">
              {triage}
              {selected && reinforcements}
            </div>
          </div>
        </section>
        <aside className="rail rail-right" aria-label="Plan">
          {planPanel}
        </aside>
      </main>
      {dialogs}
    </div>
  )
}
