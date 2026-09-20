import { describe, it, expect } from 'vitest'
import { validateRepoUrl } from './validateRepoUrl'
import { scoreColor, scoreLabel } from './score'
import { sortBySeverity } from './severity'
import { formatDate, timeAgo } from './date'

describe('validateRepoUrl', () => {
  it.each([
    'https://github.com/pallets/flask',
    'https://github.com/pallets/flask.git',
    'https://github.com/pallets/flask/',
    'https://github.com/pallets/flask/tree/main/src',
    '  https://github.com/pallets/flask  ',
  ])('accepts %s', (url) => {
    expect(validateRepoUrl(url)).toBeNull()
  })

  it.each([
    '',
    'hello',
    'http://github.com/pallets/flask',
    'https://gitlab.com/pallets/flask',
    'https://github.com/pallets',
    'https://github.com/pallets/flask/issues',
  ])('rejects "%s"', (url) => {
    expect(typeof validateRepoUrl(url)).toBe('string')
  })

  it('rejects null and undefined', () => {
    expect(validateRepoUrl(null)).not.toBeNull()
    expect(validateRepoUrl(undefined)).not.toBeNull()
  })
})

describe('scoreColor and scoreLabel', () => {
  it('uses green for 80-100', () => {
    expect(scoreColor(100)).toBe('green')
    expect(scoreColor(80)).toBe('green')
    expect(scoreLabel(80)).toBe('Healthy')
  })
  it('uses amber for 50-79', () => {
    expect(scoreColor(79)).toBe('amber')
    expect(scoreColor(50)).toBe('amber')
    expect(scoreLabel(50)).toBe('Needs attention')
  })
  it('uses red for 0-49', () => {
    expect(scoreColor(49)).toBe('red')
    expect(scoreColor(0)).toBe('red')
    expect(scoreLabel(0)).toBe('At risk')
  })
})

describe('sortBySeverity', () => {
  it('orders CRITICAL, HIGH, MEDIUM, LOW', () => {
    const list = [
      { severity: 'LOW' },
      { severity: 'CRITICAL' },
      { severity: 'MEDIUM' },
      { severity: 'HIGH' },
    ]
    expect(sortBySeverity(list).map((v) => v.severity)).toEqual(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
  })
  it('does not change the original array', () => {
    const list = [{ severity: 'LOW' }, { severity: 'HIGH' }]
    sortBySeverity(list)
    expect(list[0].severity).toBe('LOW')
  })
  it('puts unknown severities last', () => {
    const list = [{ severity: 'WEIRD' }, { severity: 'LOW' }]
    expect(sortBySeverity(list)[0].severity).toBe('LOW')
  })
})

describe('formatDate and timeAgo', () => {
  it('formats a valid date', () => {
    const text = formatDate('2026-09-20T12:00:00Z')
    expect(text).toContain('2026')
    expect(text).toContain('Sep')
  })
  it('handles invalid dates', () => {
    expect(formatDate('not a date')).toBe('-')
    expect(timeAgo('not a date')).toBe('-')
  })
  it('describes recent times', () => {
    const now = new Date('2026-09-20T12:00:00Z').getTime()
    expect(timeAgo('2026-09-20T11:59:30Z', now)).toBe('just now')
    expect(timeAgo('2026-09-20T11:55:00Z', now)).toBe('5 minutes ago')
    expect(timeAgo('2026-09-20T11:00:00Z', now)).toBe('1 hour ago')
    expect(timeAgo('2026-09-17T12:00:00Z', now)).toBe('3 days ago')
  })
})