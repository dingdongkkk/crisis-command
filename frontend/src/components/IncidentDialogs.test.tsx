import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ApiResult, ConsoleApi } from '../api/types'
import { snapshotT10 } from '../mocks/mockApi'
import { DuplicateDialog, MedicalIdDialog } from './IncidentDialogs'

type IncidentApi = NonNullable<ConsoleApi['incidents']>
const ok = <T,>(body: T): ApiResult<T> => ({ ok: true, status: 200, replayed: false, body })

function fakeApi(access: ApiResult<never> | ReturnType<typeof ok>) {
  const calls: unknown[][] = []
  const api: IncidentApi = {
    confirmFact: async (...args) => (calls.push(['confirm', ...args]), ok({ sequence: 70 })),
    resolveDuplicate: async (...args) => (calls.push(['resolve', ...args]), ok({ sequence: 71 })),
    medicalAccess: async (...args) => (calls.push(['access', ...args]), access as never),
  }
  return { api, calls }
}

describe('DuplicateDialog', () => {
  it('requires a reason and links the report to the original incident', async () => {
    const snapshot = snapshotT10()
    const [original, second] = snapshot.incidents
    if (!original || !second) throw new Error('fixture')
    const candidate = { ...second, report_ids: ['rpt_0099'], duplicate_candidate_of: [original.incident_id] }
    const { api, calls } = fakeApi(ok({}))
    const done = vi.fn()
    const user = userEvent.setup()
    render(<DuplicateDialog api={api} snapshot={snapshot} candidate={candidate} onClose={() => undefined} onDone={done} />)
    const link = screen.getByRole('button', { name: 'Same emergency — link' })
    expect(link).toBeDisabled()
    await user.type(screen.getByLabelText(/Reason/), 'Same vehicle, same caller location')
    await user.click(link)
    expect(calls[0]?.slice(0, 4)).toEqual([
      'resolve',
      original.incident_id,
      candidate.report_ids[0],
      { expected_session_id: snapshot.session_id, resolution: 'linked', reason_text: 'Same vehicle, same caller location' },
    ])
    expect(done).toHaveBeenCalledWith(expect.stringContaining('linked'))
  })
})

describe('MedicalIdDialog', () => {
  const snapshot = snapshotT10()
  const incident = snapshot.incidents[0]
  if (!incident) throw new Error('fixture')

  it('explains a denial by its 0008 reason and shows no values', async () => {
    const denied: ApiResult<never> = {
      ok: false,
      status: 403,
      problem: { type: 'x', title: 'Medical profile access denied', status: 403, code: 'PROFILE_ACCESS_DENIED', reason: 'CALLER_IS_PATIENT_UNKNOWN' } as never,
    }
    const { api } = fakeApi(denied)
    const user = userEvent.setup()
    render(<MedicalIdDialog api={api} snapshot={snapshot} incident={incident} onClose={() => undefined} />)
    await user.type(screen.getByLabelText(/Medical ID reference/), 'mprof_syn_0001')
    await user.type(screen.getByLabelText(/Reason for access/), 'Allergy check')
    await user.click(screen.getByRole('button', { name: 'Request access' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('not confirmed that the caller is the patient')
    expect(screen.queryByRole('region', { name: 'Medical ID values' })).not.toBeInTheDocument()
  })

  it('confirms caller-is-patient and shows granted synthetic values', async () => {
    const { api, calls } = fakeApi(ok({ profile_ref: 'mprof_syn_0001', values: { allergies: ['SYNTHETIC: penicillin'] } }))
    const user = userEvent.setup()
    render(<MedicalIdDialog api={api} snapshot={snapshot} incident={incident} onClose={() => undefined} />)
    await user.click(screen.getByRole('button', { name: 'Confirm yes' }))
    expect(calls[0]?.[0]).toBe('confirm')
    expect(calls[0]?.[2]).toBe('caller_is_patient')
    await user.type(screen.getByLabelText(/Medical ID reference/), 'mprof_syn_0001')
    await user.type(screen.getByLabelText(/Reason for access/), 'Allergy check')
    await user.click(screen.getByRole('button', { name: 'Request access' }))
    expect(await screen.findByRole('region', { name: 'Medical ID values' })).toHaveTextContent('Allergies: SYNTHETIC: penicillin')
  })
})
