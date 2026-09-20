import { useState } from 'react'
import DataTable from './DataTable'
import Badge from './Badge'
import SeverityBadge from './SeverityBadge'
import { severityRank } from '../utils/severity'

const UPDATE_TONE = { major: 'red', minor: 'amber', patch: 'green' }
const UPDATE_RANK = { major: 0, minor: 1, patch: 2 }
const CATEGORY_LABEL = {
  strong_copyleft: 'Strong copyleft',
  network_copyleft: 'Network copyleft',
  unknown: 'Unknown',
}
const CATEGORY_TONE = { strong_copyleft: 'orange', network_copyleft: 'red', unknown: 'slate' }

const VULN_COLUMNS = [
  { key: 'package', label: 'Package' },
  { key: 'version', label: 'Version' },
  {
    key: 'cve_id',
    label: 'CVE',
    render: (r) => (
      <a href={`https://osv.dev/vulnerability/${r.cve_id}`} target="_blank" rel="noreferrer" className="text-blue-700 underline">{r.cve_id}</a>
    ),
  },
  {
    key: 'severity',
    label: 'Severity',
    sortValue: (r) => severityRank(r.severity),
    render: (r) => <SeverityBadge severity={r.severity} />,
  },
  { key: 'fixed_version', label: 'Fixed in', render: (r) => r.fixed_version || 'No fix yet' },
  { key: 'title', label: 'Title' },
]

const OUTDATED_COLUMNS = [
  { key: 'package', label: 'Package' },
  { key: 'current', label: 'Current' },
  { key: 'latest', label: 'Latest' },
  {
    key: 'update_type',
    label: 'Update type',
    sortValue: (r) => UPDATE_RANK[r.update_type] ?? 99,
    render: (r) => <Badge tone={UPDATE_TONE[r.update_type] || 'slate'}>{r.update_type}</Badge>,
  },
]

const LICENSE_COLUMNS = [
  { key: 'package', label: 'Package' },
  { key: 'license', label: 'License' },
  {
    key: 'category',
    label: 'Category',
    render: (r) => (
      <Badge tone={CATEGORY_TONE[r.category] || 'slate'}>{CATEGORY_LABEL[r.category] || r.category}</Badge>
    ),
  },
  { key: 'reason', label: 'Reason' },
]

const TABS = [
  {
    id: 'vulnerabilities',
    label: 'Vulnerabilities',
    columns: VULN_COLUMNS,
    defaultSortKey: 'severity',
    empty: 'No known vulnerabilities found.',
  },
  {
    id: 'outdated',
    label: 'Outdated',
    columns: OUTDATED_COLUMNS,
    defaultSortKey: 'update_type',
    empty: 'All dependencies are up to date.',
  },
  {
    id: 'license_issues',
    label: 'Licenses',
    columns: LICENSE_COLUMNS,
    defaultSortKey: null,
    empty: 'No license issues found.',
  },
]

export default function FindingsTabs({ result }) {
  const [activeId, setActiveId] = useState('vulnerabilities')
  const tab = TABS.find((t) => t.id === activeId)
  const rows = result[tab.id] || []

  return (
    <section className="rounded-2xl bg-white shadow">
      <div role="tablist" aria-label="Scan findings" className="flex overflow-x-auto border-b border-slate-200">
        {TABS.map((t) => {
          const selected = t.id === activeId
          const count = (result[t.id] || []).length
          return (
            <button
              key={t.id}
              type="button"
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={selected}
              aria-controls={`panel-${t.id}`}
              onClick={() => setActiveId(t.id)}
              className={`shrink-0 whitespace-nowrap px-4 py-3 font-semibold focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-500 ${
                selected ? 'border-b-2 border-orange-600 text-orange-700' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {t.label}
              <span className="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-800">{count}</span>
            </button>
          )
        })}
      </div>
      <div role="tabpanel" id={`panel-${tab.id}`} aria-labelledby={`tab-${tab.id}`}>
        <DataTable
          key={tab.id}
          columns={tab.columns}
          rows={rows}
          defaultSortKey={tab.defaultSortKey}
          emptyMessage={tab.empty}
        />
      </div>
    </section>
  )
}