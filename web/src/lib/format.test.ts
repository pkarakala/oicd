import { describe, expect, it } from 'vitest'
import { fmt, formatLength, marginColor, niceStep, num, signed } from './format'

describe('display formatting', () => {
  it('formats lengths in the unit that suits them', () => {
    expect(formatLength(37.5, 'mm')).toBe('37.5 mm')
    expect(formatLength(2286, 'mm')).toBe('2.286 m')
    expect(formatLength(0.45, 'mm')).toBe('450 µm')
    expect(formatLength(15, 'um')).toBe('15 µm')
    expect(formatLength(220, 'nm')).toBe('220 nm')
    expect(formatLength(0, 'mm')).toBe('0 mm')
    expect(formatLength(-50, 'mm')).toBe('−50 mm')
  })

  it('picks 1, 2, 5 steps', () => {
    expect(niceStep(140)).toBe(100)
    expect(niceStep(0.31)).toBe(0.2)
    expect(niceStep(6)).toBe(5)
  })

  it('prints numbers like the engine', () => {
    expect(num(4.6875)).toBe('4.6875')
    expect(num(-1.0016000000000003)).toBe('−1.0016')
    expect(signed(0.4992)).toBe('+0.4992')
    expect(fmt(-0.00001)).toBe('0.0000')
  })

  it('looks a margin up in the API bins without deciding the color', () => {
    const bins = [
      { lo_db: null, hi_db: -1e-9, color: 'red' },
      { lo_db: -1e-9, hi_db: 1e-9, color: 'gray' },
      { lo_db: 1e-9, hi_db: null, color: 'blue' },
    ]
    expect(marginColor(bins, -0.5)).toBe('red')
    expect(marginColor(bins, -4e-16)).toBe('gray')
    expect(marginColor(bins, 2)).toBe('blue')
  })
})
