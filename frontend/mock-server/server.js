import express from 'express'

const app = express()
app.use(express.json())

const PORT = 8000
const DAY = 24 * 60 * 60 * 1000
const QUEUED_MS = 2000 // queued for 2s
const RUNNING_MS = 6000 // running until 6s (4s of running), then done or failed

// ---------- Sample result data (Section 2.4) ----------
const VULNS = [
  { package: 'minimist', version: '1.2.5', cve_id: 'CVE-2021-44906', severity: 'CRITICAL', fixed_version: '1.2.6', title: 'Prototype pollution in minimist' },
  { package: 'lodash', version: '4.17.15', cve_id: 'CVE-2021-23337', severity: 'HIGH', fixed_version: '4.17.21', title: 'Command injection in lodash template' },
  { package: 'lodash', version: '4.17.15', cve_id: 'CVE-2020-8203', severity: 'HIGH', fixed_version: '4.17.19', title: 'Prototype pollution in zipObjectDeep' },
  { package: 'node-fetch', version: '2.6.0', cve_id: 'CVE-2022-0235', severity: 'HIGH', fixed_version: '2.6.7', title: 'Exposure of sensitive information to an unauthorized actor' },
  { package: 'express', version: '4.16.0', cve_id: 'CVE-2024-29041', severity: 'MEDIUM', fixed_version: '4.19.2', title: 'Open redirect in express' },
  { package: 'jinja2', version: '2.11.2', cve_id: 'CVE-2020-28493', severity: 'MEDIUM', fixed_version: '2.11.3', title: 'Regular expression denial of service in Jinja2' },
  { package: 'requests', version: '2.25.0', cve_id: 'CVE-2023-32681', severity: 'MEDIUM', fixed_version: '2.31.0', title: 'Proxy-Authorization header leak' },
  { package: 'django', version: '2.2.0', cve_id: 'CVE-2019-12308', severity: 'MEDIUM', fixed_version: '2.2.2', title: 'XSS in AdminURLFieldWidget' },
  { package: 'ws', version: '7.4.0', cve_id: 'CVE-2021-32640', severity: 'MEDIUM', fixed_version: '7.4.6', title: 'ReDoS in Sec-Websocket-Protocol header' },
  { package: 'debug', version: '2.6.8', cve_id: 'CVE-2017-16137', severity: 'LOW', fixed_version: '2.6.9', title: 'Regular expression denial of service in debug' },
  { package: 'cookie', version: '0.3.1', cve_id: 'CVE-2024-47764', severity: 'LOW', fixed_version: null, title: 'Cookie accepts out of bounds characters' },
  { package: 'brace-expansion', version: '1.1.11', cve_id: 'CVE-2025-5889', severity: 'LOW', fixed_version: '1.1.12', title: 'Regular expression denial of service in brace-expansion' },
]

const OUTDATED = [
  { package: 'axios', current: '0.21.0', latest: '1.7.2', update_type: 'major' },
  { package: 'node-fetch', current: '2.6.0', latest: '3.3.2', update_type: 'major' },
  { package: 'django', current: '2.2.0', latest: '5.0.6', update_type: 'major' },
  { package: 'express', current: '4.16.0', latest: '4.19.2', update_type: 'minor' },
  { package: 'ws', current: '7.4.0', latest: '7.5.10', update_type: 'minor' },
  { package: 'requests', current: '2.25.0', latest: '2.32.3', update_type: 'minor' },
  { package: 'lodash', current: '4.17.15', latest: '4.17.21', update_type: 'patch' },
  { package: 'click', current: '8.1.6', latest: '8.1.7', update_type: 'patch' },
]

const LICENSE_ISSUES = [
  { package: 'pylint', license: 'GPL-2.0-or-later', category: 'strong_copyleft', reason: 'Strong copyleft license in a permissive (MIT) project' },
  { package: 'some-agpl-lib', license: 'AGPL-3.0-only', category: 'network_copyleft', reason: 'Network copyleft license in a permissive (MIT) project' },
  { package: 'legacy-widget', license: 'Unknown', category: 'unknown', reason: 'License could not be determined, review manually' },
]

const WARNINGS = ['Registry lookup failed for 2 packages', 'Trivy unavailable, used OSV.dev']

// Section 2.6 formula
function computeScore(s, majorOutdated) {
  const raw =
    100 -
    Math.min(15 * s.critical, 60) -
    Math.min(8 * s.high, 30) -
    Math.min(3 * s.medium, 15) -
    Math.min(1 * s.low, 5) -
    Math.min(2 * majorOutdated, 10) -
    Math.min(10 * s.license_issues, 20)
  return Math.max(0, Math.min(100, Math.round(raw)))
}

function buildRichResult() {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 }
  VULNS.forEach((v) => {
    counts[v.severity.toLowerCase()] += 1
  })
  const summary = {
    total_dependencies: 34,
    ...counts,
    outdated: OUTDATED.length,
    license_issues: LICENSE_ISSUES.length,
  }
  const majorOutdated = OUTDATED.filter((o) => o.update_type === 'major').length
  return {
    score: computeScore(summary, majorOutdated),
    summary,
    vulnerabilities: VULNS,
    outdated: OUTDATED,
    license_issues: LICENSE_ISSUES,
    warnings: WARNINGS,
  }
}

const RICH_RESULT = buildRichResult()

const EMPTY_RESULT = {
  score: 100,
  summary: { total_dependencies: 12, critical: 0, high: 0, medium: 0, low: 0, outdated: 0, license_issues: 0 },
  vulnerabilities: [],
  outdated: [],
  license_issues: [],
  warnings: [],
}

// ---------- In-memory data ----------
const repos = []
const scans = new Map()
let nextScanId = 1

function iso(ms) {
  return new Date(ms).toISOString()
}

function seedRepo(url, scores) {
  const repo = { repo_id: repos.length + 1, url }
  repos.push(repo)
  scores.forEach((score, i) => {
    const daysAgo = (scores.length - i) * 7
    scans.set(nextScanId, {
      scan_id: nextScanId,
      repo_id: repo.repo_id,
      repo_url: url,
      created_ms: Date.now() - daysAgo * DAY,
      kind: 'normal',
      score,
    })
    nextScanId += 1
  })
}

seedRepo('https://github.com/pallets/flask', [52, 58, 61, 66, 72, 78, 84])
seedRepo('https://github.com/expressjs/express', [88, 85, 80, 74, 70, 66])
seedRepo('https://github.com/lodash/lodash', [45, 48, 44, 52, 61, 67, 71, 90])

// ---------- Helpers ----------
const URL_RE = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+?)(?:\.git)?(?:\/(?:tree\/.*)?)?$/i

function normalizeUrl(url) {
  const m = URL_RE.exec(String(url || '').trim())
  if (!m) return null
  return `https://github.com/${m[1]}/${m[2]}`.toLowerCase()
}

function viewScan(scan) {
  const elapsed = Date.now() - scan.created_ms
  let status = 'queued'
  if (elapsed >= RUNNING_MS) status = scan.kind === 'fail' ? 'failed' : 'done'
  else if (elapsed >= QUEUED_MS) status = 'running'

  const finished = status === 'done' || status === 'failed'
  let result = null
  if (status === 'done') {
    const base = scan.kind === 'empty' ? EMPTY_RESULT : RICH_RESULT
    result = scan.score != null ? { ...base, score: scan.score } : base
  }
  return {
    scan_id: scan.scan_id,
    repo_id: scan.repo_id,
    repo_url: scan.repo_url,
    status,
    created_at: iso(scan.created_ms),
    finished_at: finished ? iso(scan.created_ms + RUNNING_MS) : null,
    error: status === 'failed' ? 'Repository not found or it is private.' : null,
    result,
  }
}

function historyFor(repoId) {
  return [...scans.values()]
    .filter((s) => s.repo_id === repoId)
    .sort((a, b) => a.created_ms - b.created_ms)
    .map(viewScan)
    .filter((v) => v.status === 'done')
    .map((v) => ({ scan_id: v.scan_id, date: v.created_at, score: v.result.score }))
}

// ---------- Endpoints (Section 2.5) ----------
app.get('/health', (req, res) => {
  res.json({ status: 'ok' })
})

app.post('/api/scans', (req, res) => {
  const url = normalizeUrl(req.body && req.body.repo_url)
  if (!url) {
    return res.status(400).json({ detail: 'Invalid repository URL. Use https://github.com/owner/repo' })
  }
  let repo = repos.find((r) => r.url === url)
  if (!repo) {
    repo = { repo_id: repos.length + 1, url }
    repos.push(repo)
  }
  const kind = url.includes('fail') ? 'fail' : url.includes('empty') ? 'empty' : 'normal'
  const scan = {
    scan_id: nextScanId,
    repo_id: repo.repo_id,
    repo_url: url,
    created_ms: Date.now(),
    kind,
    score: null,
  }
  nextScanId += 1
  scans.set(scan.scan_id, scan)
  res.status(202).json({ scan_id: scan.scan_id, repo_id: scan.repo_id, status: 'queued' })
})

app.get('/api/scans/:id', (req, res) => {
  const scan = scans.get(Number(req.params.id))
  if (!scan) return res.status(404).json({ detail: 'Scan not found' })
  res.json(viewScan(scan))
})

app.get('/api/repos', (req, res) => {
  res.json(
    repos.map((repo) => {
      const hist = historyFor(repo.repo_id)
      const last = hist[hist.length - 1]
      return {
        repo_id: repo.repo_id,
        url: repo.url,
        latest_score: last ? last.score : null,
        last_scan_at: last ? last.date : null,
        scan_count: hist.length,
      }
    }),
  )
})

app.get('/api/repos/:id/history', (req, res) => {
  const repoId = Number(req.params.id)
  if (!repos.find((r) => r.repo_id === repoId)) {
    return res.status(404).json({ detail: 'Repository not found' })
  }
  res.json(historyFor(repoId))
})

// Errors always use { detail }
app.use((err, req, res, next) => { // eslint-disable-line no-unused-vars
  res.status(400).json({ detail: 'Malformed request' })
})

app.listen(PORT, () => {
  console.log(`Mock API running on http://localhost:${PORT}`)
})