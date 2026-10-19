import { describe, expect, it } from 'vitest'
import type { Link } from '../api/client'
import { HISTORY_LIMIT, createExplorerStore } from './store'

const link = (name: string) => ({ name }) as unknown as Link

describe('explorer store', () => {
  it('starts from the URL', () => {
    const store = createExplorerStore('?scene=passage_l20&sel=l20g.eic&tab=inference')
    const s = store.getState()
    expect([s.scene, s.selection, s.dockTab]).toEqual(['passage_l20', 'l20g.eic', 'inference'])
  })

  it('changing scene clears selection, visibility, tour and section, and fits the view', () => {
    const store = createExplorerStore()
    const a = store.getState()
    a.select('rack.posts')
    a.toggleHidden('rack.busbar')
    a.setSection('x')
    a.setTourStop(2)
    a.setScene('switch_tray')
    const s = store.getState()
    expect(s.selection).toBeNull()
    expect(s.hidden).toEqual([])
    expect(s.sectionAxis).toBeNull()
    expect(s.tourStop).toBeNull()
    expect(s.camera?.command).toEqual({ kind: 'fit' })
  })

  it('undo and redo design edits, and a new edit clears redo', () => {
    const store = createExplorerStore()
    const a = store.getState()
    a.loadLink(link('start'))
    a.edit((d) => ({ ...d, link: link('one') }))
    a.edit((d) => ({ ...d, link: link('two') }))
    a.undo()
    expect(store.getState().design.link?.name).toBe('one')
    a.undo()
    expect(store.getState().design.link?.name).toBe('start')
    a.undo() // nothing left: no change
    expect(store.getState().design.link?.name).toBe('start')
    a.redo()
    expect(store.getState().design.link?.name).toBe('one')
    a.edit((d) => ({ ...d, lanes: 4 }))
    expect(store.getState().future).toEqual([])
    a.redo()
    expect(store.getState().design.lanes).toBe(4)
  })

  it('keeps a bounded history', () => {
    const store = createExplorerStore()
    for (let i = 0; i < HISTORY_LIMIT + 20; i++) store.getState().edit((d) => ({ ...d, lanes: i }))
    expect(store.getState().past).toHaveLength(HISTORY_LIMIT)
  })

  it('allows one hypothesis per group', () => {
    const store = createExplorerStore()
    const groups: Record<string, string> = { H_dir: 'bw', H_agg: 'bw', H_2U: 'height' }
    const groupOf = (id: string) => groups[id] ?? ''
    const a = store.getState()
    a.toggleHypothesis('H_dir', 'bw', groupOf)
    a.toggleHypothesis('H_2U', 'height', groupOf)
    a.toggleHypothesis('H_agg', 'bw', groupOf)
    expect(store.getState().hypotheses).toEqual(['H_2U', 'H_agg'])
    a.toggleHypothesis('H_agg', 'bw', groupOf)
    expect(store.getState().hypotheses).toEqual(['H_2U'])
  })

  it('measure keeps two picks, a third starts over', () => {
    const store = createExplorerStore()
    const a = store.getState()
    a.setMeasure(true)
    a.addMeasurePoint([0, 0, 0])
    a.addMeasurePoint([1, 0, 0])
    expect(store.getState().measurePoints).toHaveLength(2)
    a.addMeasurePoint([2, 0, 0])
    expect(store.getState().measurePoints).toEqual([[2, 0, 0]])
  })

  it('Escape closes the innermost mode first', () => {
    const store = createExplorerStore()
    const a = store.getState()
    a.select('rack.posts')
    a.setMeasure(true)
    a.setPaletteOpen(true)
    a.escape()
    expect(store.getState().paletteOpen).toBe(false)
    a.escape()
    expect(store.getState().measure).toBe(false)
    a.escape()
    expect(store.getState().selection).toBeNull()
  })
})
