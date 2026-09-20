import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ResultsPage from './ResultsPage'
import { getScan } from '../api/client'

vi.mock('../api/client', () => ({
  getScan: vi.fn(),
  submitScan: vi.fn(),
}))

const base = {
  scan_id: 1,
  repo_id: 1,
  repo_url: 'https://github.com/pallets/flask',
  created_at: '2026-09-20T10:00:00Z',
  finished_at: '2026-09-20T10:00:06Z',
  error: null,
  result: null,
}

const doneResult = {
  score: 72,
  summary: { total_dependencies: 34, critical: 0, high: 1, medium: 0, low: 0, outdated: 1, license_issues: 0 },
  vulnerabilities: [
    {
      package: 'lodash',
      version: '4.17.15',
      cve_id: 'CVE-2021-23337',
      severity: 'HIGH',
      fixed_version: '4.17.21',
      title: 'Command injection in lodash template',
    },
  ],
  outdated: [{ package: 'express', current: '4.16.0', latest: '4.19.2', update_type: 'minor' }],
  license_issues: [],
  warnings: ['Registry lookup failed for 1 package'],
}

const emptyResult = {
  score: 100,
  summary: { total_dependencies: 12, critical: 0, high: 0, medium: 0, low: 0, outdated: 0, license_issues: 0 },
  vulnerabilities: [],
  outdated: [],
  license_issues: [],
  warnings: [],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/scans/1']}>
      <Routes>
        <Route path="/scans/:scanId" element={<ResultsPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ResultsPage', () => {
  beforeEach(() => {
    getScan.mockReset()
  })

  it('shows the queued state', async () => {
    getScan.mockResolvedValue({ ...base, status: 'queued' })
    renderPage()
    expect(await screen.findByText(/Waiting in the queue/)).toBeTruthy()
  })

  it('shows the running state', async () => {
    getScan.mockResolvedValue({ ...base, status: 'running' })
    renderPage()
    expect(await screen.findByText(/Scanning your dependencies/)).toBeTruthy()
  })

  it('shows the failed state with the error and a retry button', async () => {
    getScan.mockResolvedValue({ ...base, status: 'failed', error: 'Repository not found or it is private.' })
    renderPage()
    expect(await screen.findByText('Scan failed')).toBeTruthy()
    expect(screen.getByText('Repository not found or it is private.')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy()
  })

  it('shows the done state with score, warnings and findings', async () => {
    getScan.mockResolvedValue({ ...base, status: 'done', result: doneResult })
    renderPage()
    expect(await screen.findByText('72')).toBeTruthy()
    expect(screen.getByText('Registry lookup failed for 1 package')).toBeTruthy()
    expect(screen.getByText('CVE-2021-23337')).toBeTruthy()
  })

  it('shows friendly empty states when there are no findings', async () => {
    getScan.mockResolvedValue({ ...base, status: 'done', result: emptyResult })
    renderPage()
    expect(await screen.findByText('100')).toBeTruthy()
    expect(screen.getByText('No known vulnerabilities found.')).toBeTruthy()
  })
})