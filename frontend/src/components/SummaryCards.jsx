const CARDS = [
  { key: 'critical', label: 'Critical', color: 'text-red-700' },
  { key: 'high', label: 'High', color: 'text-orange-700' },
  { key: 'medium', label: 'Medium', color: 'text-yellow-700' },
  { key: 'low', label: 'Low', color: 'text-blue-700' },
  { key: 'outdated', label: 'Outdated', color: 'text-amber-700' },
  { key: 'license_issues', label: 'License issues', color: 'text-purple-700' },
]

export default function SummaryCards({ summary }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {CARDS.map((c) => (
        <div key={c.key} className="rounded-xl bg-slate-50 p-4 text-center">
          <div className={`text-3xl font-bold ${c.color}`}>{summary[c.key] ?? 0}</div>
          <div className="mt-1 text-sm text-slate-600">{c.label}</div>
        </div>
      ))}
    </div>
  )
}