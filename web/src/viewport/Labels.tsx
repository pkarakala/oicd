// Leader-line labels and grid labels as one DOM layer over the canvas. A probe inside the canvas
// projects each 3D anchor to the screen whenever the camera, the size or the anchors change.

import { useThree } from '@react-three/fiber'
import { useEffect, useMemo } from 'react'
import * as THREE from 'three'
import type { Overlay, Palette, Part, SceneInfo } from '../api/client'
import { formatLength, niceStep, num, signed } from '../lib/format'
import { partBounds } from '../lib/geometry'
import { useExplorer } from '../state/store'

export interface Anchor {
  id: string
  kind: 'part' | 'grid'
  position: [number, number, number] // three.js world coordinates
  title: string
  value?: string
  status?: string // a verdict key: its color and label come from the API palette
  color?: string // the value's color from the API (margin bin)
  part?: string
}

export interface Projected {
  x: number
  y: number
  visible: boolean
}

export function partAnchors(parts: readonly Part[], overlay: Overlay | undefined, opts: { explode: number; hidden: string[]; isolated: string | null; overlays: boolean }): Anchor[] {
  const values = new Map((opts.overlays ? (overlay?.values ?? []) : []).map((v) => [v.part, v]))
  const out: Anchor[] = []
  for (const part of parts) {
    if (!part.label) continue
    if (opts.hidden.includes(part.id) || (opts.isolated !== null && opts.isolated !== part.id)) continue
    const box = partBounds(part, opts.explode)
    const value = values.get(part.id)
    let text: string | undefined
    if (value?.margin_db !== undefined && value.margin_db !== null) text = `${signed(value.margin_db)} dB`
    else if (value?.power_mw !== undefined && value.power_mw !== null) text = `${num(value.power_mw, 5)} mW`
    out.push({
      id: part.id,
      kind: 'part',
      position: [(box.min.x + box.max.x) / 2, box.max.y, (box.min.z + box.max.z) / 2],
      title: part.label,
      value: text,
      status: value?.verdict ?? undefined,
      color: value?.color ?? undefined,
      part: part.id,
    })
  }
  return out
}

export function gridAnchors(bounds: THREE.Box3, unit: SceneInfo['unit']): Anchor[] {
  const size = bounds.getSize(new THREE.Vector3())
  const center = bounds.getCenter(new THREE.Vector3())
  const span = Math.max(size.x, size.z, size.y * 0.5)
  const step = niceStep(span / 2.5)
  const out: Anchor[] = []
  const start = Math.ceil((center.x - span * 0.75) / step) * step
  for (let x = start; x <= center.x + span * 0.75; x += step) {
    out.push({
      id: `grid:${x}`,
      kind: 'grid',
      position: [x, bounds.min.y, bounds.max.z + step * 0.25],
      title: formatLength(Math.abs(x) < step * 1e-9 ? 0 : x, unit, 4),
    })
  }
  return out
}

/** Inside the canvas: projects anchors to the viewport's pixel coordinates. */
export function Projector({ anchors, onProject }: { anchors: Anchor[]; onProject: (p: Map<string, Projected>) => void }) {
  const camera = useThree((s) => s.camera)
  const size = useThree((s) => s.size)
  useEffect(() => {
    let frame = 0
    const project = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const out = new Map<string, Projected>()
        const v = new THREE.Vector3()
        for (const a of anchors) {
          v.set(...a.position).project(camera)
          out.set(a.id, { x: ((v.x + 1) / 2) * size.width, y: ((1 - v.y) / 2) * size.height, visible: v.z > -1 && v.z < 1 })
        }
        onProject(out)
      })
    }
    project()
    window.addEventListener('oicd:camera', project)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('oicd:camera', project)
    }
  }, [anchors, camera, size.width, size.height, onProject])
  return null
}

const LEADERS = [22, 50, 78, 106, 134, 162] // px: longer leaders lift a label clear of its neighbors

/** Greedy declutter: each label takes the shortest leader whose box overlaps no placed label;
 * a label with no free slot is hidden (null) unless it is the selection. */
export function placeLabels(anchors: Anchor[], positions: Map<string, Projected>, keep: string | null): Map<string, number | null> {
  const placed: { x0: number; x1: number; y0: number; y1: number }[] = []
  const out = new Map<string, number | null>()
  const parts = anchors
    .filter((a) => a.kind === 'part' && positions.get(a.id)?.visible)
    .sort((a, b) => (a.part === keep ? -1 : b.part === keep ? 1 : (positions.get(b.id)?.y ?? 0) - (positions.get(a.id)?.y ?? 0)))
  for (const a of parts) {
    const p = positions.get(a.id)!
    const width = Math.max(a.title.length * 7.2, (a.value?.length ?? 0) * 6.8 + (a.status ? 62 : 0)) + 20
    const height = a.value ? 38 : 24
    let chosen: number | null = null
    for (const leader of LEADERS) {
      const box = { x0: p.x - width / 2, x1: p.x + width / 2, y0: p.y - leader - height, y1: p.y - leader }
      if (!placed.some((q) => box.x0 < q.x1 && q.x0 < box.x1 && box.y0 < q.y1 && q.y0 < box.y1)) {
        chosen = leader
        break
      }
    }
    if (chosen === null && a.part === keep) chosen = LEADERS[0]!
    if (chosen !== null) placed.push({ x0: p.x - width / 2, x1: p.x + width / 2, y0: p.y - chosen - height, y1: p.y - chosen })
    out.set(a.id, chosen)
  }
  return out
}

/** Outside the canvas: the labels themselves. */
export function LabelLayer({ anchors, positions, palette }: { anchors: Anchor[]; positions: Map<string, Projected>; palette: Palette }) {
  const select = useExplorer((s) => s.select)
  const selection = useExplorer((s) => s.selection)
  const statuses = useMemo(() => new Map(palette.status.map((s) => [s.key, s])), [palette])
  const leaders = useMemo(() => placeLabels(anchors, positions, selection), [anchors, positions, selection])
  return (
    <div className="label-layer" aria-hidden={false}>
      {anchors.map((a) => {
        const p = positions.get(a.id)
        if (p === undefined || !p.visible) return null
        if (a.kind === 'grid') {
          return (
            <span key={a.id} className="grid-label" style={{ left: p.x, top: p.y }}>
              {a.title}
            </span>
          )
        }
        const status = a.status ? statuses.get(a.status) : undefined
        const leader = leaders.get(a.id)
        if (leader === null) return null // no room: shown when selected, or in the Inspector
        return (
          <button
            key={a.id}
            type="button"
            className={`leader ${selection === a.part ? 'is-selected' : ''}`}
            style={{ left: p.x, top: p.y, ['--leader' as string]: `${leader ?? 22}px` }}
            onClick={() => a.part && select(a.part)}
            aria-label={`Select ${a.title}`}
          >
            <span className="leader-text">{a.title}</span>
            {a.value && (
              <span className="leader-value">
                {a.color && <span className="chip-dot" style={{ background: a.color }} aria-hidden />}
                {a.value}
                {status && (
                  <span className="leader-status" style={{ color: status.color }}>
                    {status.label}
                  </span>
                )}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
