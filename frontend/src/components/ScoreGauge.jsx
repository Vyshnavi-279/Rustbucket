import { scoreColor, scoreLabel } from '../utils/score'

const STROKE = { green: '#15803d', amber: '#b45309', red: '#b91c1c' }
const PILL = {
  green: 'bg-green-100 text-green-800',
  amber: 'bg-amber-100 text-amber-800',
  red: 'bg-red-100 text-red-800',
}

export default function ScoreGauge({ score }) {
  const radius = 72
  const circumference = 2 * Math.PI * radius
  const value = Math.max(0, Math.min(100, score))
  const offset = circumference * (1 - value / 100)
  const color = scoreColor(value)
  const label = scoreLabel(value)

  return (
    <div className="flex flex-col items-center">
      <svg
        width="180"
        height="180"
        viewBox="0 0 180 180"
        role="img"
        aria-label={`Health score ${value} out of 100, ${label}`}
      >
        <circle cx="90" cy="90" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="14" />
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke={STROKE[color]}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 90 90)"
        />
        <text
          x="90"
          y="90"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="48"
          fontWeight="700"
          fill={STROKE[color]}
        >
          {value}
        </text>
      </svg>
      <span className={`mt-2 rounded-full px-3 py-1 text-sm font-semibold ${PILL[color]}`}>{label}</span>
    </div>
  )
}