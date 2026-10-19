// Shareable URL state: the view, never the physics. Pure encode/decode so it can be unit-tested.

export const DOCK_TABS = [
  'budget',
  'spectrum',
  'design',
  'tray',
  'upstream',
  'yield',
  'inference',
  'spec',
  'physics',
] as const
export type DockTab = (typeof DOCK_TABS)[number]
export type Theme = 'light' | 'dark'
export type Projection = 'perspective' | 'orthographic'
export type Axis = 'x' | 'y' | 'z'
export const SPECTRUM_HYPOTHESES = ['H_fsr18', 'H_fsr32'] as const
export type SpectrumHypothesis = (typeof SPECTRUM_HYPOTHESES)[number]

export interface UrlState {
  scene: string
  selection: string | null
  dockTab: DockTab
  projection: Projection
  theme: Theme
  explode: number
  sectionAxis: Axis | null
  sectionOffset: number
  overlayCase: string | null
  isolationDb: number | null
  spectrumHypothesis: SpectrumHypothesis
  tint: boolean
  hypotheses: string[]
  still: boolean // pulses stopped (screenshots and reduced motion)
}

export const URL_DEFAULTS: UrlState = {
  scene: 'reference_rack',
  selection: null,
  dockTab: 'spec',
  projection: 'perspective',
  theme: 'light',
  explode: 0,
  sectionAxis: null,
  sectionOffset: 0,
  overlayCase: null,
  isolationDb: null,
  spectrumHypothesis: 'H_fsr18',
  tint: false,
  hypotheses: [],
  still: false,
}

const NAME = /^[a-z0-9_]+$/
const PART = /^[a-z0-9_]+(\.[a-z0-9_]+)+$/
const POINT = /^[\w .()+-]{1,80}$/ // trace-point names in the link scene
const HYPOTHESIS = /^H_[A-Za-z0-9_]+$/
const CASE = /^H_[A-Za-z0-9_]+$/

function round(value: number, digits = 4): string {
  return String(Number(value.toFixed(digits)))
}

export function encodeUrl(state: UrlState): string {
  const p = new URLSearchParams()
  const d = URL_DEFAULTS
  if (state.scene !== d.scene) p.set('scene', state.scene)
  if (state.selection !== null) p.set('sel', state.selection)
  if (state.dockTab !== d.dockTab) p.set('tab', state.dockTab)
  if (state.projection !== d.projection) p.set('proj', 'ortho')
  if (state.theme !== d.theme) p.set('theme', state.theme)
  if (state.explode !== d.explode) p.set('explode', round(state.explode, 3))
  if (state.sectionAxis !== null) p.set('section', `${state.sectionAxis}:${round(state.sectionOffset)}`)
  if (state.overlayCase !== null) p.set('case', state.overlayCase)
  if (state.isolationDb !== null) p.set('iso', round(state.isolationDb, 2))
  if (state.spectrumHypothesis !== d.spectrumHypothesis) p.set('fsr', state.spectrumHypothesis)
  if (state.tint) p.set('tint', '1')
  if (state.hypotheses.length > 0) p.set('hyp', state.hypotheses.join(','))
  if (state.still) p.set('still', '1')
  const text = p.toString()
  return text ? `?${text}` : ''
}

function number(text: string | null, lo: number, hi: number): number | undefined {
  if (text === null || text.trim() === '') return undefined
  const value = Number(text)
  return Number.isFinite(value) && value >= lo && value <= hi ? value : undefined
}

/** Fields present and valid in the query string; anything invalid is ignored. */
export function decodeUrl(search: string): Partial<UrlState> {
  const p = new URLSearchParams(search)
  const out: Partial<UrlState> = {}
  const scene = p.get('scene')
  if (scene !== null && NAME.test(scene)) out.scene = scene
  const sel = p.get('sel')
  if (sel !== null && (PART.test(sel) || POINT.test(sel))) out.selection = sel
  const tab = p.get('tab')
  if (tab !== null && (DOCK_TABS as readonly string[]).includes(tab)) out.dockTab = tab as DockTab
  if (p.get('proj') === 'ortho') out.projection = 'orthographic'
  const theme = p.get('theme')
  if (theme === 'dark' || theme === 'light') out.theme = theme
  const explode = number(p.get('explode'), 0, 1)
  if (explode !== undefined) out.explode = explode
  const section = p.get('section')
  if (section !== null) {
    const [axis, offset] = section.split(':')
    const value = number(offset ?? null, -0.5, 0.5)
    if ((axis === 'x' || axis === 'y' || axis === 'z') && value !== undefined) {
      out.sectionAxis = axis
      out.sectionOffset = value
    }
  }
  const overlayCase = p.get('case')
  if (overlayCase !== null && CASE.test(overlayCase)) out.overlayCase = overlayCase
  const iso = number(p.get('iso'), 0, 60)
  if (iso !== undefined) out.isolationDb = iso
  const fsr = p.get('fsr')
  if (fsr !== null && (SPECTRUM_HYPOTHESES as readonly string[]).includes(fsr)) {
    out.spectrumHypothesis = fsr as SpectrumHypothesis
  }
  if (p.get('tint') === '1') out.tint = true
  if (p.get('still') === '1') out.still = true
  const hyp = p.get('hyp')
  if (hyp !== null) {
    const ids = hyp.split(',').filter((h) => HYPOTHESIS.test(h))
    if (ids.length > 0) out.hypotheses = ids
  }
  return out
}
