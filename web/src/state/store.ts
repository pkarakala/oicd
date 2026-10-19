// Explorer state (zustand): what is shown and the design edits, with undo/redo for the edits.
// Physics never lives here; edits are inputs that the engine evaluates.

import { create } from 'zustand'
import type { Link } from '../api/client'
import {
  type Axis,
  type DockTab,
  type Projection,
  type SpectrumHypothesis,
  type Theme,
  type UrlState,
  URL_DEFAULTS,
  decodeUrl,
} from './url'

export type ViewName = 'front' | 'top' | 'right' | 'iso'
export type CameraCommand =
  | { kind: 'view'; view: ViewName }
  | { kind: 'fit' }
  | { kind: 'fitSelection' }
  | { kind: 'part'; part: string }

export interface Design {
  link: Link | null
  lanes: number
  laneEdits: Record<number, number> // lane index → patch connector loss (dB) in the Tray view
}

export type Vec3 = [number, number, number]

export interface ExplorerState extends UrlState {
  hovered: string | null
  hidden: string[]
  isolated: string | null
  measure: boolean
  measurePoints: Vec3[]
  labels: boolean
  overlays: boolean
  clean: boolean
  tourStop: number | null
  paletteOpen: boolean
  shortcutsOpen: boolean
  camera: { command: CameraCommand; nonce: number } | null
  design: Design
  past: Design[]
  future: Design[]
}

export interface ExplorerActions {
  setScene: (scene: string) => void
  select: (id: string | null) => void
  hover: (id: string | null) => void
  toggleHidden: (id: string) => void
  isolate: (id: string | null) => void
  showAll: () => void
  setDockTab: (tab: DockTab) => void
  setTheme: (theme: Theme) => void
  setProjection: (projection: Projection) => void
  setSection: (axis: Axis | null) => void
  setSectionOffset: (offset: number) => void
  setExplode: (explode: number) => void
  setMeasure: (on: boolean) => void
  addMeasurePoint: (point: Vec3) => void
  setFlag: (flag: 'tint' | 'labels' | 'overlays' | 'clean' | 'still', on: boolean) => void
  setTourStop: (stop: number | null) => void
  setPaletteOpen: (open: boolean) => void
  setShortcutsOpen: (open: boolean) => void
  setOverlayCase: (overlayCase: string | null) => void
  setIsolation: (db: number | null) => void
  setSpectrumHypothesis: (h: SpectrumHypothesis) => void
  toggleHypothesis: (id: string, group: string, groupOf: (id: string) => string) => void
  command: (command: CameraCommand) => void
  loadLink: (link: Link) => void
  edit: (update: (design: Design) => Design) => void
  undo: () => void
  redo: () => void
  escape: () => void
}

export const HISTORY_LIMIT = 100
export const DEFAULT_LANES = 8

export function initialState(search = ''): ExplorerState {
  return {
    ...URL_DEFAULTS,
    ...decodeUrl(search),
    hovered: null,
    hidden: [],
    isolated: null,
    measure: false,
    measurePoints: [],
    labels: true,
    overlays: true,
    clean: false,
    tourStop: null,
    paletteOpen: false,
    shortcutsOpen: false,
    camera: null,
    design: { link: null, lanes: DEFAULT_LANES, laneEdits: {} },
    past: [],
    future: [],
  }
}

let nonce = 0

export const createExplorerStore = (search = '') =>
  create<ExplorerState & ExplorerActions>()((set, get) => ({
    ...initialState(search),
    setScene: (scene) =>
      set((s) =>
        s.scene === scene
          ? s
          : {
              scene,
              selection: null,
              hovered: null,
              hidden: [],
              isolated: null,
              tourStop: null,
              measurePoints: [],
              sectionAxis: null,
              sectionOffset: 0,
              explode: 0,
              camera: { command: { kind: 'fit' }, nonce: ++nonce },
            },
      ),
    select: (selection) => set({ selection }),
    hover: (hovered) => set((s) => (s.hovered === hovered ? s : { hovered })),
    toggleHidden: (id) =>
      set((s) => ({ hidden: s.hidden.includes(id) ? s.hidden.filter((h) => h !== id) : [...s.hidden, id] })),
    isolate: (isolated) => set({ isolated }),
    showAll: () => set({ hidden: [], isolated: null }),
    setDockTab: (dockTab) => set({ dockTab }),
    setTheme: (theme) => set({ theme }),
    setProjection: (projection) => set({ projection }),
    setSection: (sectionAxis) => set({ sectionAxis, sectionOffset: 0 }),
    setSectionOffset: (sectionOffset) => set({ sectionOffset: Math.min(Math.max(sectionOffset, -0.5), 0.5) }),
    setExplode: (explode) => set({ explode: Math.min(Math.max(explode, 0), 1) }),
    setMeasure: (measure) => set({ measure, measurePoints: [] }),
    addMeasurePoint: (point) =>
      set((s) => ({ measurePoints: s.measurePoints.length >= 2 ? [point] : [...s.measurePoints, point] })),
    setFlag: (flag, on) => set({ [flag]: on } as Pick<ExplorerState, typeof flag>),
    setTourStop: (tourStop) => set({ tourStop }),
    setPaletteOpen: (paletteOpen) => set({ paletteOpen }),
    setShortcutsOpen: (shortcutsOpen) => set({ shortcutsOpen }),
    setOverlayCase: (overlayCase) => set({ overlayCase }),
    setIsolation: (isolationDb) => set({ isolationDb }),
    setSpectrumHypothesis: (spectrumHypothesis) => set({ spectrumHypothesis }),
    toggleHypothesis: (id, group, groupOf) =>
      set((s) => {
        if (s.hypotheses.includes(id)) return { hypotheses: s.hypotheses.filter((h) => h !== id) }
        // at most one hypothesis per group (the engine rejects two alternatives)
        const kept = group ? s.hypotheses.filter((h) => groupOf(h) !== group) : s.hypotheses
        return { hypotheses: [...kept, id] }
      }),
    command: (command) => set({ camera: { command, nonce: ++nonce } }),
    loadLink: (link) => set((s) => ({ design: { ...s.design, link } })),
    edit: (update) =>
      set((s) => ({
        past: [...s.past, s.design].slice(-HISTORY_LIMIT),
        future: [],
        design: update(s.design),
      })),
    undo: () =>
      set((s) => {
        const previous = s.past[s.past.length - 1]
        if (previous === undefined) return s
        return { past: s.past.slice(0, -1), future: [s.design, ...s.future], design: previous }
      }),
    redo: () =>
      set((s) => {
        const [next, ...rest] = s.future
        if (next === undefined) return s
        return { past: [...s.past, s.design], future: rest, design: next }
      }),
    escape: () => {
      const s = get()
      if (s.paletteOpen || s.shortcutsOpen) set({ paletteOpen: false, shortcutsOpen: false })
      else if (s.measure) set({ measure: false, measurePoints: [] })
      else if (s.tourStop !== null) set({ tourStop: null })
      else set({ selection: null, isolated: null })
    },
  }))

export const useExplorer = createExplorerStore(typeof window === 'undefined' ? '' : window.location.search)

export function urlState(s: ExplorerState): UrlState {
  return {
    scene: s.scene,
    selection: s.selection,
    dockTab: s.dockTab,
    projection: s.projection,
    theme: s.theme,
    explode: s.explode,
    sectionAxis: s.sectionAxis,
    sectionOffset: s.sectionOffset,
    overlayCase: s.overlayCase,
    isolationDb: s.isolationDb,
    spectrumHypothesis: s.spectrumHypothesis,
    tint: s.tint,
    hypotheses: s.hypotheses,
    still: s.still,
  }
}
