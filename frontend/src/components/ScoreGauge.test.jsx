import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScoreGauge from './ScoreGauge'

describe('ScoreGauge', () => {
  it('renders the score number and its label', () => {
    render(<ScoreGauge score={52} />)
    expect(screen.getByText('52')).toBeTruthy()
    expect(screen.getByText('Needs attention')).toBeTruthy()
  })

  it.each([
    [95, 'Healthy'],
    [65, 'Needs attention'],
    [20, 'At risk'],
  ])('shows the right label for %i', (score, label) => {
    render(<ScoreGauge score={score} />)
    expect(screen.getByText(label)).toBeTruthy()
  })

  it('has an accessible description', () => {
    render(<ScoreGauge score={17} />)
    expect(screen.getByRole('img', { name: /17 out of 100/ })).toBeTruthy()
  })

  it('clamps scores outside 0-100', () => {
    render(<ScoreGauge score={150} />)
    expect(screen.getByText('100')).toBeTruthy()
  })
})