// Physics overlays from GET /overlay/{scene}: thin emissive lines per wavelength channel (false
// color, constant pixel width at every zoom level) and pulses whose brightness is the API's linear
// power, dimming at each loss. Ghost pulses (BiDi reflections) use the same scale, so a ghost far
// below the signal is not visible. Light whose power is not disclosed is drawn faint, without
// pulses.

import { Line } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import type { LightPath, Overlay, Part } from '../api/client'
import { centerline, instanceCenters, toThree } from '../lib/geometry'
import { useExplorer } from '../state/store'

const LINE_GAIN = 2.2 // static line emission at brightness 1 (bloom threshold is luminance 1)
const PULSE_GAIN = 7.0
const PULSES = 3 // per light path and instance
const PERIOD_S = 2.4 // one transit
const LINE_PX = 2.2
const PULSE_PX = 10
const STEPS = 48 // samples per centerline

type Sample = LightPath['samples'][number]

let dotTexture: THREE.Texture | null = null
function dot(): THREE.Texture {
  if (dotTexture !== null) return dotTexture
  const size = 64
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')
  if (ctx !== null) {
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    g.addColorStop(0, 'rgba(255,255,255,1)')
    g.addColorStop(0.45, 'rgba(255,255,255,0.85)')
    g.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, size, size)
  }
  dotTexture = new THREE.CanvasTexture(canvas)
  return dotTexture
}

function lateralOffset(curve: THREE.Curve<THREE.Vector3>, u: number, amount: number): THREE.Vector3 {
  if (amount === 0) return new THREE.Vector3()
  const tangent = curve.getTangentAt(Math.min(Math.max(u, 0), 1))
  const ref = Math.abs(tangent.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0)
  return new THREE.Vector3().crossVectors(tangent, ref).normalize().multiplyScalar(amount)
}

/** Brightness of the light at u: the last sample passed in the direction of travel. */
export function brightnessAt(samples: readonly Sample[], u: number): number {
  const first = samples[0]
  const last = samples[samples.length - 1]
  if (first === undefined || last === undefined) return 0
  const sign = last.at >= first.at ? 1 : -1
  let value = first.brightness
  for (const s of samples) if ((u - s.at) * sign >= -1e-9) value = s.brightness
  return value
}

interface PathProps {
  path: LightPath
  part: Part
  slot: number
  slots: number
  explode: number
}

function PathObject({ path, part, slot, slots, explode }: PathProps) {
  const still = useExplorer((s) => s.still)
  const invalidate = useThree((s) => s.invalidate)
  const dpr = useThree((s) => s.viewport.dpr)
  const centers = useMemo(() => {
    const all = instanceCenters(part, 0)
    return path.instances.length === 0 ? all : path.instances.map((i) => all[i]).filter((c) => c !== undefined)
  }, [part, path.instances])
  const curves = useMemo(() => centers.map((c) => centerline(part, c)), [centers, part])
  const lateral = slots > 1 ? (slot - (slots - 1) / 2) * (part.size[0] / 2) * 0.55 : 0
  const base = useMemo(() => new THREE.Color(path.color), [path.color])
  const undisclosed = path.direction === 'none'
  const first = path.samples[0]
  const last = path.samples[path.samples.length - 1]
  const lo = Math.min(first?.at ?? 0, last?.at ?? 1)
  const hi = Math.max(first?.at ?? 0, last?.at ?? 1)

  // static line: pairs of points along each centerline, colored by the stretch's brightness
  const segments = useMemo(() => {
    if (path.kind === 'ghost') return null
    const points: THREE.Vector3[] = []
    const colors: [number, number, number][] = []
    for (const curve of curves) {
      for (let i = 0; i < STEPS; i++) {
        const u0 = lo + ((hi - lo) * i) / STEPS
        const u1 = lo + ((hi - lo) * (i + 1)) / STEPS
        const b = brightnessAt(path.samples, (u0 + u1) / 2) * (undisclosed ? 1 : LINE_GAIN)
        const c = base.clone().multiplyScalar(b)
        points.push(curve.getPointAt(u0).add(lateralOffset(curve, u0, lateral)), curve.getPointAt(u1).add(lateralOffset(curve, u1, lateral)))
        colors.push([c.r, c.g, c.b], [c.r, c.g, c.b])
      }
    }
    return { points, colors }
  }, [curves, path, lo, hi, lateral, base, undisclosed])

  const pulses = useRef<THREE.Points>(null)
  const count = undisclosed ? 0 : curves.length * PULSES
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3))
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(count * 3), 3))
    return g
  }, [count])
  useEffect(() => () => geometry.dispose(), [geometry])
  const color = useMemo(() => new THREE.Color(), [])

  useFrame(({ clock }) => {
    const points = pulses.current
    if (points === null || count === 0 || first === undefined || last === undefined) return
    const position = geometry.getAttribute('position') as THREE.BufferAttribute
    const colors = geometry.getAttribute('color') as THREE.BufferAttribute
    const t = still ? 0.37 : clock.elapsedTime / PERIOD_S
    curves.forEach((curve, k) => {
      for (let j = 0; j < PULSES; j++) {
        const phase = (((t + j / PULSES) % 1) + 1) % 1
        const u = Math.min(Math.max(first.at + (last.at - first.at) * phase, 0), 1)
        const p = curve.getPointAt(u).add(lateralOffset(curve, u, lateral))
        position.setXYZ(k * PULSES + j, p.x, p.y, p.z)
        color.copy(base).multiplyScalar(brightnessAt(path.samples, u) * PULSE_GAIN)
        colors.setXYZ(k * PULSES + j, color.r, color.g, color.b)
      }
    })
    position.needsUpdate = true
    colors.needsUpdate = true
    geometry.computeBoundingSphere()
    if (!still) invalidate()
  })

  const offset = toThree(part.explode).multiplyScalar(explode)
  return (
    <group position={offset}>
      {segments && segments.points.length > 0 && (
        <Line
          points={segments.points}
          vertexColors={segments.colors}
          segments
          lineWidth={undisclosed ? 1.1 : LINE_PX}
          toneMapped={false}
          transparent
          opacity={undisclosed ? 0.55 : 1}
          raycast={() => null}
        />
      )}
      {count > 0 && (
        <points ref={pulses} geometry={geometry} frustumCulled={false} raycast={() => null}>
          <pointsMaterial
            size={(path.kind === 'ghost' ? PULSE_PX * 0.8 : PULSE_PX) * dpr}
            sizeAttenuation={false}
            vertexColors
            map={dot()}
            transparent
            depthWrite={false}
            toneMapped={false}
          />
        </points>
      )}
    </group>
  )
}

export function LightPaths({ overlay, parts }: { overlay: Overlay; parts: readonly Part[] }) {
  const explode = useExplorer((s) => s.explode)
  const hidden = useExplorer((s) => s.hidden)
  const isolated = useExplorer((s) => s.isolated)
  const byId = useMemo(() => new Map(parts.map((p) => [p.id, p])), [parts])
  // paths on one part sit side by side; a ghost rides in its transmitter's lane
  const lanes = useMemo(() => {
    const keyOf = (p: LightPath) => `${p.part}:${p.instances.join(',')}`
    const count = new Map<string, number>()
    const lane = overlay.paths.map((p) => {
      if (p.kind === 'ghost') return -1
      const n = count.get(keyOf(p)) ?? 0
      count.set(keyOf(p), n + 1)
      return n
    })
    return overlay.paths.map((p, k) => {
      let slot = lane[k] ?? 0
      if (p.kind === 'ghost') {
        const twin = overlay.paths.findIndex((q) => q.kind !== 'ghost' && q.part === p.part && q.color === p.color)
        slot = twin >= 0 ? (lane[twin] ?? 0) : 0
      }
      return { slot, slots: count.get(keyOf(p)) ?? 1 }
    })
  }, [overlay])
  return (
    <group name="light-paths">
      {overlay.paths.map((path, k) => {
        const part = byId.get(path.part)
        if (part === undefined || hidden.includes(part.id) || (isolated !== null && isolated !== part.id)) return null
        const { slot, slots } = lanes[k] ?? { slot: 0, slots: 1 }
        return <PathObject key={`${overlay.scene}:${k}`} path={path} part={part} slot={slot} slots={slots} explode={explode} />
      })}
    </group>
  )
}
