import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getHistory, listRepos, submitScan } from '../api/client'
import Badge from '../components/Badge'
import { scoreColor } from '../utils/score'
import { formatDate } from '../utils/date'

function HistoryView({ repoId }) {
  const navigate = useNavigate()
  const [history, setHistory] = useState(null)
  const [repo, setRepo] = useState(null)
  const [error, setError] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([getHistory(repoId), listRepos()])
      .then(([hist, repos]) => {
        if (cancelled) return
        setHistory(hist)
        setRepo(repos.find((r) => String(r.repo_id) === String(repoId)) || null)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [repoId])

  async function handleScanAgain() {
    if (!repo) return
    setScanning(true)
    setScanError(null)
    try {
      const scan = await submitScan(repo.url)
      navigate(`/scans/${scan.scan_id}`)
    } catch (err) {
      setScanError(err.message)
      setScanning(false)
    }
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
          {error}
        </div>
        <Link to="/history" className="text-blue-700 underline">Back to history</Link>
      </div>
    )
  }

  if (history === null) {
    return (
      <div className="space-y-4" aria-hidden="true">
        <div className="h-10 w-64 animate-pulse rounded bg-slate-200" />
        <div className="h-72 animate-pulse rounded-2xl bg-slate-200" />
      </div>
    )
  }

  const dateById = new Map(history.map((h) => [h.scan_id, h.date]))
  const newestFirst = [...history].reverse()

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">
            {repo ? repo.url.replace('https://github.com/', '') : `Repository ${repoId}`}
          </h1>
          <p className="text-slate-600">Health score over time</p>
        </div>
        <button
          type="button"
          onClick={handleScanAgain}
          disabled={!repo || scanning}
          className="rounded-lg bg-orange-700 px-4 py-2 font-semibold text-white hover:bg-orange-800 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-60"
        >
          {scanning ? 'Starting…' : 'Scan again'}
        </button>
      </header>

      {scanError && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-red-800">
          {scanError}
        </div>
      )}

      {history.length === 0 ? (
        <div className="rounded-2xl bg-white p-6 text-slate-600 shadow">
          No finished scans for this repository yet. Use <strong>Scan again</strong> to run one.
        </div>
      ) : (
        <>
          <section className="rounded-2xl bg-white p-4 shadow" aria-label="Score trend chart">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="scan_id"
                    tickFormatter={(id) => formatDate(dateById.get(id))}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis domain={[0, 100]} ticks={[0, 25, 50, 80, 100]} tick={{ fontSize: 12 }} />
                  <Tooltip
                    labelFormatter={(id) => formatDate(dateById.get(id))}
                    formatter={(value) => [value, 'Score']}
                  />
                  <ReferenceLine y={50} stroke="#b91c1c" strokeDasharray="5 5" />
                  <ReferenceLine y={80} stroke="#15803d" strokeDasharray="5 5" />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#c2410c"
                    strokeWidth={2}
                    dot={{ r: 5 }}
                    activeDot={{ r: 7 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Dashed lines mark the thresholds: green from 80, red below 50.
            </p>
            {history.length === 1 && (
              <p className="mt-2 text-sm text-slate-700">Scan again to see a trend.</p>
            )}
          </section>

          <section className="overflow-x-auto rounded-2xl bg-white shadow">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-700">
                <tr>
                  <th scope="col" className="px-4 py-3 font-semibold">Date</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Score</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Results</th>
                </tr>
              </thead>
              <tbody>
                {newestFirst.map((h) => (
                  <tr key={h.scan_id} className="border-t border-slate-100">
                    <td className="px-4 py-3">{formatDate(h.date)}</td>
                    <td className="px-4 py-3">
                      <Badge tone={scoreColor(h.score)}>{h.score}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/scans/${h.scan_id}`} className="text-blue-700 underline">
                        View results
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  )
}

export default function RepoHistoryPage() {
  const { repoId } = useParams()
  // key resets all state when the repo changes
  return <HistoryView key={repoId} repoId={repoId} />
}