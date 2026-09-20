const ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }

// Returns a new array sorted CRITICAL, HIGH, MEDIUM, LOW. Unknown values go last.
export function sortBySeverity(list) {
  const rank = (item) => (item.severity in ORDER ? ORDER[item.severity] : 99)
  return [...list].sort((a, b) => rank(a) - rank(b))
}