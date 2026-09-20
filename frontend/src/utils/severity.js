const ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }

export function severityRank(severity) {
  return severity in ORDER ? ORDER[severity] : 99
}

// Returns a new array sorted CRITICAL, HIGH, MEDIUM, LOW. Unknown values go last.
export function sortBySeverity(list) {
  return [...list].sort((a, b) => severityRank(a.severity) - severityRank(b.severity))
}