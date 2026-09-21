import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { submitScan, listRepos } from '../api/client'
import { validateRepoUrl } from '../utils/validateRepoUrl'
import { scoreColor } from '../utils/score'
import { timeAgo } from '../utils/date'

const EXAMPLES = [
  'https://github.com/pallets/flask',
  'https://github.com/expressjs/express',
  'https://github.com/lodash/lodash',
]

const BADGE = {
  green: 'bg-green-100 text-green-800',
  amber: 'bg-amber-100 text-amber-800',
  red: 'bg-red-100 text-red-800',
}

function Spinner() {
  return (
    <span
      className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
      aria-hidden="true"
    />
  )
}

export default function SubmitPage() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [fieldError, setFieldError] = useState(null)
  const [apiError, setApiError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [repos, setRepos] = useState(null)

  useEffect(() => {
    let cancelled = false
    listRepos()
      .then((data) => {
        if (!cancelled) setRepos(data)
      })
      .catch(() => {
        if (!cancelled) setRepos([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setApiError(null)
    const problem = validateRepoUrl(url)
    setFieldError(problem)
    if (problem) return

    setLoading(true)
    try {
      const scan = await submitScan(url.trim())
      navigate(`/scans/${scan.scan_id}`)
    } catch (err) {
      setApiError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow">
        <h1 className="text-3xl font-bold">Check your dependency health</h1>
        <p className="mt-1 text-slate-600">Don&apos;t let your dependencies rust away.</p>

        <form onSubmit={handleSubmit} className="mt-6" noValidate>
          <label htmlFor="repo-url" className="block text-sm font-medium">
            GitHub repository URL
          </label>
          <input
            id="repo-url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            aria-invalid={fieldError ? 'true' : 'false'}
            aria-describedby={fieldError ? 'repo-url-error' : undefined}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
          {fieldError && (
            <p id="repo-url-error" className="mt-1 text-sm text-red-700">
              {fieldError}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-orange-700 px-4 py-2 font-semibold text-white hover:bg-orange-800 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-60"
          >
            {loading && <Spinner />}
            {loading ? 'Scanning…' : 'Scan'}
          </button>
        </form>

        {apiError && (
          <div role="alert" className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-red-800">
            {apiError}
          </div>
        )}

        <div className="mt-6">
          <p className="text-sm text-slate-500">Try an example:</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => {
                  setUrl(ex)
                  setFieldError(null)
                }}
                className="rounded-full border border-slate-300 px-3 py-1 text-sm hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                {ex.replace('https://github.com/', '')}
              </button>
            ))}
          </div>
        </div>
      </div>

      <section aria-labelledby="recent-heading">
        <h2 id="recent-heading" className="mb-3 text-lg font-semibold">
          Recently scanned
        </h2>
        {repos === null && (
          <div className="grid gap-3 sm:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
        )}
        {repos && repos.length === 0 && (
          <p className="text-slate-500">No scans yet. Scan your first repository above.</p>
        )}
        {repos && repos.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-3">
            {repos.map((r) => (
              <Link
                key={r.repo_id}
                to={`/history/${r.repo_id}`}
                className="rounded-xl bg-white p-4 shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <div className="truncate font-medium">{r.url.replace('https://github.com/', '')}</div>
                <div className="mt-2 flex items-center justify-between text-sm">
                  {r.latest_score != null ? (
                    <span className={`rounded-full px-2 py-0.5 font-semibold ${BADGE[scoreColor(r.latest_score)]}`}>
                      Score {r.latest_score}
                    </span>
                  ) : (
                    <span className="text-slate-500">No score</span>
                  )}
                  <span className="text-slate-500">{r.last_scan_at ? timeAgo(r.last_scan_at) : ''}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}