import { render, screen } from '@testing-library/react'
import { App } from './App'
import health from './test/fixtures/health.json'
import { validateContract, type HealthResponse } from './contracts'

describe('App shell', () => {
  it('always states the simulation boundary', () => {
    render(<App />)
    expect(screen.getByRole('status')).toHaveTextContent(/SIMULATION/)
    expect(screen.getByRole('status')).toHaveTextContent(/No real calls, dispatch or notifications/)
    expect(screen.getByRole('heading', { name: 'Crisis Command' })).toBeInTheDocument()
    expect(screen.getByText(/backend not connected/)).toBeInTheDocument()
  })

  it('renders a contract-valid health payload', () => {
    expect(validateContract('HealthResponse', health)).toEqual({ valid: true, errors: [] })
    render(<App health={health as HealthResponse} />)
    expect(screen.getByText(/backend ok · mode simulation/)).toBeInTheDocument()
  })
})
