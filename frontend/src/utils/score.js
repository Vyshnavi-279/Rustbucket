// Section 2.6: 80-100 green | 50-79 amber | 0-49 red
export function scoreColor(score) {
  if (score >= 80) return 'green'
  if (score >= 50) return 'amber'
  return 'red'
}

export function scoreLabel(score) {
  if (score >= 80) return 'Healthy'
  if (score >= 50) return 'Needs attention'
  return 'At risk'
}