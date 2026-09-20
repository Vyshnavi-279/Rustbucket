import FindingsTabs from '../components/FindingsTabs'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getScan, submitScan } from '../api/client'
import ScoreGauge from '../components/ScoreGauge'
import SummaryCards from '../components/SummaryCards'
import { formatDate, timeAgo } from '../utils/date'
  

const POLL_MS = 2000

function Spinner({ dark = false }) {
  return (
    <span
      className={`inline-block h-5 w-5 animate-spin rounded-full border-2 border-t-transparent ${
        dark ? 'border-slate-600' : 'border-white'
      }`}
      aria-hidden="true"
    />
  )
}

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

function ProgressCard({ status, elapsed }) {
  return (
    <div className="rounded-2xl bg-white p-6 shadow" role="status" aria-live="polite">
      <div className="flex items-center gap-3">
        <Spinner dark />
        <div>
          <p className="font-semibold">
            {status === 'running' ? 'Scanning your dependencies…' : 'Waiting in the queue…'}
          </p>
          <p className="mt-1 break-words text-slate-600">
            Status: {status} · Elapsed: {formatElapsed(elapsed)}
          </p>
        </div>
      </div>
    </div>
  )
}

function SkeletonResults() {
  return (
    <div className="space-y-4" aria-hidden="true">
      <div className="h-48 animate-pulse rounded-2xl bg-slate-200" />
      <div className="h-64 animate-pulse rounded-2xl bg-slate-200" />
    </div>
  )
}

function FailedCard({ error, onRetry, retrying, retryError }) {
  return (
    <div role="alert" className="rounded-2xl border border-red-300 bg-red-50 p-6">
      <h1 className="text-xl font-bold text-red-800">Scan failed</h1>
      <p className="mt-2 text-red-800">{error || 'Something went wrong while scanning.'}</p>
      {retryError && <p className="mt-2 text-sm text-red-800">{retryError}</p>}
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          onClick={onRetry}
          disabled={retrying}
          className="rounded-lg bg-orange-700 px-4 py-2 font-semibold text-white hover:bg-orange-800 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-60"
        >
          {retrying ? 'Retrying…' : 'Try again'}
        </button>
        <Link
          to="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-semibold hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          Back
        </Link>
      </div>
    </div>
  )
}

function DoneView({ scan }) {
  const { result } = scan
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Scan results</h1>
        <p className="mt-1 text-slate-600">
          <a href={scan.repo_url} target="_blank" rel="noreferrer" className="text-blue-700 underline">{scan.repo_url}</a>
          {' · '}
          <span title={formatDate(scan.finished_at)}>scanned {timeAgo(scan.finished_at)}</span>
          {' · '}
          {result.summary.total_dependencies} dependencies
        </p>
      </header>

      <section className="grid gap-6 rounded-2xl bg-white p-6 shadow md:grid-cols-[220px_1fr]">
        <ScoreGauge score={result.score} />
        <SummaryCards summary={result.summary} />
      </section>

      {result.warnings && result.warnings.length > 0 && (
        <div role="status" className="rounded-lg border border-yellow-300 bg-yellow-50 p-4 text-yellow-900">
          <p className="font-semibold">Warnings</p>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <FindingsTabs result={result} />
    </div>
  )
}

function ResultsView({ scanId }) {
  const navigate = useNavigate()
  const [scan, setScan] = useState(null)
  const [pollError, setPollError] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [retrying, setRetrying] = useState(false)
  const [retryError, setRetryError] = useState(null)

  const active = !scan || scan.status === 'queued' || scan.status === 'running'

  // Poll immediately, then every 2 seconds, until done or failed.
  useEffect(() => {
    let cancelled = false
    let timer

    async function poll() {
      try {
        const data = await getScan(scanId)
        if (cancelled) return
        setScan(data)
        setPollError(null)
        if (data.status === 'done' || data.status === 'failed') return
      } catch (err) {
        if (cancelled) return
        setPollError(err.message)
      }
      timer = setTimeout(poll, POLL_MS)
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [scanId])

  // Elapsed-time counter while the scan is in progress.
  useEffect(() => {
    if (!active) return
    const id = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [active])

  async function handleRetry() {
    setRetrying(true)
    setRetryError(null)
    try {
      const next = await submitScan(scan.repo_url)
      navigate(`/scans/${next.scan_id}`)
    } catch (err) {
      setRetryError(err.message)
      setRetrying(false)
    }
  }

  return (
    <div className="space-y-6">
      {pollError && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-red-800">
          Could not refresh the scan status: {pollError} Retrying…
        </div>
      )}

      {active && (
        <>
          <ProgressCard status={scan ? scan.status : 'queued'} elapsed={elapsed} />
          <SkeletonResults />
        </>
      )}

      {scan && scan.status === 'failed' && (
        <FailedCard error={scan.error} onRetry={handleRetry} retrying={retrying} retryError={retryError} />
      )}

      {scan && scan.status === 'done' && scan.result && <DoneView scan={scan} />}
    </div>
  )
}

export default function ResultsPage() {
  const { scanId } = useParams()
  // key resets all state when the scan id changes (for example after "Try again")
  return <ResultsView key={scanId} scanId={scanId} />
}