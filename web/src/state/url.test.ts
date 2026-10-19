import { describe, expect, it } from 'vitest'
import { URL_DEFAULTS, decodeUrl, encodeUrl } from './url'

describe('URL state', () => {
  it('omits defaults', () => {
    expect(encodeUrl(URL_DEFAULTS)).toBe('')
  })

  it('round-trips every field', () => {
    const state = {
      ...URL_DEFAULTS,
      scene: 'passage_l20',
      selection: 'l20g.eic',
      dockTab: 'inference' as const,
      projection: 'orthographic' as const,
      theme: 'dark' as const,
      explode: 0.75,
      sectionAxis: 'y' as const,
      sectionOffset: -0.125,
      overlayCase: 'H_vclick_module',
      isolationDb: 12.5,
      spectrumHypothesis: 'H_fsr32' as const,
      tint: true,
      hypotheses: ['H_dir', 'H_2U'],
      still: true,
    }
    const encoded = encodeUrl(state)
    expect({ ...URL_DEFAULTS, ...decodeUrl(encoded) }).toEqual(state)
  })

  it('keeps a link-scene selection by trace-point name', () => {
    expect(decodeUrl('?scene=link&sel=patch+connector').selection).toBe('patch connector')
  })

  it('ignores invalid values', () => {
    const decoded = decodeUrl(
      '?scene=../x&tab=nope&explode=2&section=w:0.1&iso=-3&fsr=H_x&hyp=bad,H_ok&theme=blue&case=x y',
    )
    expect(decoded).toEqual({ hypotheses: ['H_ok'] })
  })

  it('clamps nothing silently: an out-of-range section offset is dropped', () => {
    expect(decodeUrl('?section=x:0.9')).toEqual({})
    expect(decodeUrl('?section=z:0.5')).toEqual({ sectionAxis: 'z', sectionOffset: 0.5 })
  })
})
