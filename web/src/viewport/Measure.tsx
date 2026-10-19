// Measure tool: two picks that snap to the picked part's feature-edge vertices, then to its edges,
// then to the surface; the distance reads in auto units (m, mm, µm, nm).

import { Html, Line } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import { useEffect } from 'react'
import * as THREE from 'three'
import type { SceneInfo } from '../api/client'
import { formatLength } from '../lib/format'
import { distance, fromThree, toThree } from '../lib/geometry'
import { useExplorer } from '../state/store'

const VERTEX_SNAP_PX = 14
const EDGE_SNAP_PX = 8

function toScreen(v: THREE.Vector3, camera: THREE.Camera, rect: DOMRect): THREE.Vector2 {
  const p = v.clone().project(camera)
  return new THREE.Vector2(((p.x + 1) / 2) * rect.width, ((1 - p.y) / 2) * rect.height)
}

/** The snapped world point for a hit on an instanced part mesh. */
export function snap(hit: THREE.Intersection, camera: THREE.Camera, rect: DOMRect, cursor: THREE.Vector2): THREE.Vector3 {
  const mesh = hit.object as THREE.InstancedMesh
  const group = mesh.parent
  const lines = group?.children.find((c) => c instanceof THREE.LineSegments) as THREE.LineSegments | undefined
  if (lines === undefined || group === null) return hit.point.clone()
  const position = lines.geometry.getAttribute('position') as THREE.BufferAttribute
  const perInstance = position.count / Math.max(mesh.count, 1)
  const first = (hit.instanceId ?? 0) * perInstance
  const world = (i: number) => new THREE.Vector3().fromBufferAttribute(position, i).applyMatrix4(lines.matrixWorld)
  let best: THREE.Vector3 | null = null
  let bestPx = VERTEX_SNAP_PX
  for (let i = first; i < first + perInstance; i++) {
    const v = world(i)
    const px = toScreen(v, camera, rect).distanceTo(cursor)
    if (px < bestPx) {
      bestPx = px
      best = v
    }
  }
  if (best !== null) return best
  bestPx = EDGE_SNAP_PX
  for (let i = first; i + 1 < first + perInstance; i += 2) {
    const a = world(i)
    const b = world(i + 1)
    const sa = toScreen(a, camera, rect)
    const sb = toScreen(b, camera, rect)
    const ab = sb.clone().sub(sa)
    const t = ab.lengthSq() === 0 ? 0 : Math.min(Math.max(cursor.clone().sub(sa).dot(ab) / ab.lengthSq(), 0), 1)
    const px = sa.clone().add(ab.multiplyScalar(t)).distanceTo(cursor)
    if (px < bestPx) {
      bestPx = px
      best = a.clone().lerp(b, t)
    }
  }
  return best ?? hit.point.clone()
}

export function Measure({ unit, radius, ink }: { unit: SceneInfo['unit']; radius: number; ink: string }) {
  const measure = useExplorer((s) => s.measure)
  const points = useExplorer((s) => s.measurePoints)
  const add = useExplorer((s) => s.addMeasurePoint)
  const camera = useThree((s) => s.camera)
  const gl = useThree((s) => s.gl)
  const scene = useThree((s) => s.scene)
  const raycaster = useThree((s) => s.raycaster)
  const invalidate = useThree((s) => s.invalidate)

  useEffect(() => {
    if (!measure) return
    const element = gl.domElement
    let down: { x: number; y: number } | null = null
    const onDown = (ev: PointerEvent) => {
      down = { x: ev.clientX, y: ev.clientY }
    }
    const onUp = (ev: PointerEvent) => {
      if (down === null || Math.hypot(ev.clientX - down.x, ev.clientY - down.y) > 4) return // a drag orbits
      const rect = element.getBoundingClientRect()
      const cursor = new THREE.Vector2(ev.clientX - rect.left, ev.clientY - rect.top)
      const ndc = new THREE.Vector2((cursor.x / rect.width) * 2 - 1, -(cursor.y / rect.height) * 2 + 1)
      raycaster.setFromCamera(ndc, camera)
      const parts = scene.getObjectByName('parts')
      if (parts === undefined) return
      const hit = raycaster.intersectObject(parts, true).find((h) => h.object instanceof THREE.InstancedMesh)
      if (hit === undefined) return
      add(fromThree(snap(hit, camera, rect, cursor)))
      invalidate()
    }
    element.addEventListener('pointerdown', onDown)
    element.addEventListener('pointerup', onUp)
    return () => {
      element.removeEventListener('pointerdown', onDown)
      element.removeEventListener('pointerup', onUp)
    }
  }, [measure, gl, camera, scene, raycaster, add, invalidate])

  if (!measure || points.length === 0) return null
  const world = points.map((p) => toThree(p))
  const dot = radius * 0.006
  const [a, b] = points
  return (
    <group name="measure">
      {world.map((p, i) => (
        <mesh key={i} position={p} raycast={() => null} renderOrder={5}>
          <sphereGeometry args={[dot, 16, 12]} />
          <meshBasicMaterial color={ink} depthTest={false} transparent opacity={0.9} />
        </mesh>
      ))}
      {a !== undefined && b !== undefined && (
        <>
          <Line points={[world[0]!, world[1]!]} color={ink} lineWidth={2} depthTest={false} transparent renderOrder={6} />
          <Html position={world[0]!.clone().lerp(world[1]!, 0.5)} center zIndexRange={[40, 30]}>
            <div className="measure-label" data-testid="measure-value">
              {formatLength(distance(a, b), unit)}
            </div>
          </Html>
        </>
      )}
    </group>
  )
}
