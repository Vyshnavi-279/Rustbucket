import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listRepos } from '../api/client'
import Badge from '../components/Badge'
import { scoreColor } from '../utils/score'
import { timeAgo } from '../utils/date'

export default function HistoryListPage() {
  const navigate = useNavigate()
  const [repos, setRepos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    listRepos()
      .then((data) => {
        if (!cancelled) setRepos(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Scan history</h1>

      {error && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-3 text-red-800">
          {error}
        </div>
      )}

      {!error && repos === null && <div className="h-40 animate-pulse rounded-2xl bg-slate-200" />}

      {repos && repos.length === 0 && (
        <div className="rounded-2xl bg-white p-6 text-slate-600 shadow">
          No repositories scanned yet. <Link to="/" className="text-blue-700 underline">Scan your first one</Link>.
        </div>
      )}

      {repos && repos.length > 0 && (
        <div className="overflow-x-auto rounded-2xl bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold">Repository</th>
                <th scope="col" className="px-4 py-3 font-semibold">Latest score</th>
                <th scope="col" className="px-4 py-3 font-semibold">Scans</th>
                <th scope="col" className="px-4 py-3 font-semibold">Last scan</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((r) => (
                <tr
                  key={r.repo_id}
                  onClick={() => navigate(`/history/${r.repo_id}`)}
                  className="cursor-pointer border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/history/${r.repo_id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium text-blue-700 underline focus:outline-none focus:ring-2 focus:ring-orange-500"
                    >
                      {r.url.replace('https://github.com/', '')}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {r.latest_score != null ? (
                      <Badge tone={scoreColor(r.latest_score)}>{r.latest_score}</Badge>
                    ) : (
                      <span className="text-slate-500">No score</span>
                    )}
                  </td>
                  <td className="px-4 py-3">{r.scan_count}</td>
                  <td className="px-4 py-3">{r.last_scan_at ? timeAgo(r.last_scan_at) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}