// Keyboard shortcuts. Typing in a field never triggers them (Escape still closes things).

import { useEffect } from 'react'
import { LINK_SCENE } from '../api/hooks'
import { useExplorer } from '../state/store'
import type { Axis } from '../state/url'

export const SHORTCUTS: [string, string][] = [
  ['⌘K / Ctrl+K', 'Command palette: products, parts, analyses, views and commands'],
  ['1 2 3 4', 'Front, top, right and isometric views'],
  ['F / Shift+F', 'Fit all / fit selection'],
  ['O', 'Perspective or orthographic'],
  ['S', 'Section view: X, Y, Z, off'],
  ['E', 'Exploded view'],
  ['M', 'Measure (two picks, snaps to vertices and edges)'],
  ['L / V / T', 'Labels / physics overlays / tint SCHEMATIC parts'],
  ['P', 'Pause or play pulses'],
  ['Enter / Backspace', 'Zoom into the selected part / up one level'],
  ['← →', 'Previous / next tour stop'],
  ['⌘Z / ⌘⇧Z', 'Undo / redo design edits'],
  ['Esc', 'Close, stop measuring, end the tour, clear the selection'],
  ['?', 'This sheet'],
]

function typing(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

const NEXT_AXIS: Record<'off' | Axis, Axis | null> = { off: 'x', x: 'y', y: 'z', z: null }

export function useShortcuts() {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const s = useExplorer.getState()
      const mod = e.metaKey || e.ctrlKey
      if (e.key === 'Escape') {
        s.escape()
        return
      }
      if (mod && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        s.setPaletteOpen(!s.paletteOpen)
        return
      }
      if (typing(e.target) || s.paletteOpen) return
      if (mod && e.key.toLowerCase() === 'z') {
        e.preventDefault()
        if (e.shiftKey) s.redo()
        else s.undo()
        return
      }
      if (mod && e.key.toLowerCase() === 'y') {
        e.preventDefault()
        s.redo()
        return
      }
      if (mod || e.altKey) return
      const views: Record<string, 'front' | 'top' | 'right' | 'iso'> = { '1': 'front', '2': 'top', '3': 'right', '4': 'iso' }
      const view = views[e.key]
      if (view) return s.command({ kind: 'view', view })
      switch (e.key) {
        case 'f':
          return s.command({ kind: 'fit' })
        case 'F':
          return s.command({ kind: 'fitSelection' })
        case 'o':
          return s.setProjection(s.projection === 'perspective' ? 'orthographic' : 'perspective')
        case 's':
          if (s.scene !== LINK_SCENE) s.setSection(NEXT_AXIS[s.sectionAxis ?? 'off'])
          return
        case 'e':
          if (s.scene !== LINK_SCENE) window.dispatchEvent(new CustomEvent('oicd:explode'))
          return
        case 'm':
          return s.setMeasure(!s.measure)
        case 'l':
          return s.setFlag('labels', !s.labels)
        case 'v':
          return s.setFlag('overlays', !s.overlays)
        case 't':
          return s.setFlag('tint', !s.tint)
        case 'p':
          return s.setFlag('still', !s.still)
        case '?':
          return s.setShortcutsOpen(!s.shortcutsOpen)
        case 'ArrowRight':
        case 'ArrowLeft':
          if (s.tourStop !== null) window.dispatchEvent(new CustomEvent('oicd:tour', { detail: e.key === 'ArrowRight' ? 1 : -1 }))
          return
        case 'Enter':
        case 'Backspace':
          window.dispatchEvent(new CustomEvent('oicd:zoom', { detail: e.key === 'Enter' ? 'in' : 'out' }))
          return
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
}
