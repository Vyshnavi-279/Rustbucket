import { useState } from 'react'

export default function DataTable({ columns, rows, defaultSortKey = null, emptyMessage }) {
  const [sortKey, setSortKey] = useState(defaultSortKey)
  const [dir, setDir] = useState('asc')

  if (rows.length === 0) {
    return (
      <div className="flex items-center gap-3 p-6 text-slate-700">
        <span
          className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 text-green-700"
          aria-hidden="true"
        >
          ✓
        </span>
        <span>{emptyMessage}</span>
      </div>
    )
  }

  function onSort(key) {
    if (key === sortKey) {
      setDir(dir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setDir('asc')
    }
  }

  const col = columns.find((c) => c.key === sortKey)
  let sorted = rows
  if (col) {
    const valueOf = (row) => (col.sortValue ? col.sortValue(row) : row[col.key])
    sorted = [...rows].sort((a, b) => {
      const av = valueOf(a)
      const bv = valueOf(b)
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      const cmp =
        typeof av === 'number' && typeof bv === 'number'
          ? av - bv
          : String(av).localeCompare(String(bv), undefined, { numeric: true })
      return dir === 'asc' ? cmp : -cmp
    })
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-700">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                aria-sort={c.key === sortKey ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}
                className="px-4 py-2 font-semibold"
              >
                <button
                  type="button"
                  onClick={() => onSort(c.key)}
                  className="flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {c.label}
                  <span aria-hidden="true" className="text-xs text-slate-400">
                    {c.key === sortKey ? (dir === 'asc' ? '▲' : '▼') : '↕'}
                  </span>
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i} className="border-t border-slate-100">
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-2 align-top">
                  {c.render ? c.render(row) : (row[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}