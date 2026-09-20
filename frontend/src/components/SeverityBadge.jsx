import Badge from './Badge'

const TONES = { CRITICAL: 'red', HIGH: 'orange', MEDIUM: 'yellow', LOW: 'blue' }

export default function SeverityBadge({ severity }) {
  return <Badge tone={TONES[severity] || 'slate'}>{severity}</Badge>
}