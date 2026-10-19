// The link view as a schematic scene (not to scale): TX engine, matings, fiber, patch
// connector, RX engine, from the FeasibilityReport. Fiber segments are colored only by the API's
// above_threshold flag (review R1); pulses dim with the API's relative_power at each element.
// With an upstream chain, the external laser and its 1:N split appear before TP2.

import { Html } from '@react-three/drei'
import { type ThreeEvent, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import type { FeasibilityReport, Palette, TracePoint } from '../api/client'
import { displayName, fmt, primaryInput } from '../lib/format'
import { useExplorer } from '../state/store'
import { partObjects } from './Parts'

export const SPACING = 2.4
const FIBER_Y = 0.55
const PULSE_GAIN = 4.5

type Shape = 'engine' | 'fau' | 'connector' | 'fiber' | 'generic'

function shapeOf(point: TracePoint): Shape {
  if (point.kind === 'reference_plane') return 'engine'
  if (/FAU/i.test(point.name)) return 'fau'
  if (/connector|patch/i.test(point.name)) return 'connector'
  if (/SMF|fiber|fibre/i.test(point.name)) return 'fiber'
  return 'generic'
}

export function linkLayout(count: number): THREE.Vector3[] {
  return Array.from({ length: count }, (_, i) => {
    const edge = i === 0 || i === count - 1
    return new THREE.Vector3((i - (count - 1) / 2) * SPACING, FIBER_Y, edge ? 0 : 0.6 * Math.sin(i * 1.7))
  })
}

export function linkBounds(report: FeasibilityReport | undefined): THREE.Box3 {
  const n = report?.power_trace.length ?? 7
  const half = ((n - 1) / 2) * SPACING + 1.2
  const laser = report?.upstream ? SPACING * 1.6 : 0
  return new THREE.Box3(new THREE.Vector3(-half - laser, 0, -1.4), new THREE.Vector3(half, 1.4, 1.4))
}

function useMaterial(palette: Palette, key: string) {
  return palette.materials.find((m) => m.key === key) ?? palette.materials[0]!
}

interface ComponentProps {
  point: TracePoint
  position: THREE.Vector3
  palette: Palette
}

function LinkComponent({ point, position, palette }: ComponentProps) {
  const select = useExplorer((s) => s.select)
  const hover = useExplorer((s) => s.hover)
  const hovered = useExplorer((s) => s.hovered === point.name)
  const group = useRef<THREE.Group>(null)
  const shape = shapeOf(point)
  const substrate = useMaterial(palette, 'organic_substrate')
  const silicon = useMaterial(palette, 'silicon')
  const glass = useMaterial(palette, 'glass')
  const polymer = useMaterial(palette, 'polymer')
  const fiber = useMaterial(palette, 'fiber')
  const emissive = hovered ? palette.muted : '#000000'
  const lift = hovered ? 0.25 : 0
  useEffect(() => {
    const object = group.current
    if (object === null) return
    partObjects.set(point.name, object)
    return () => {
      if (partObjects.get(point.name) === object) partObjects.delete(point.name)
    }
  }, [point.name])
  const handlers = {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation()
      hover(point.name)
    },
    onPointerOut: () => hover(null),
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation()
      select(point.name)
    },
  }
  const std = (m: typeof silicon) => (
    <meshStandardMaterial color={m.color} metalness={m.metalness} roughness={m.roughness} emissive={emissive} emissiveIntensity={lift} />
  )
  if (shape === 'engine') {
    return (
      <group ref={group} position={[position.x, 0, position.z]} {...handlers} name={point.name}>
        <mesh position={[0, 0.06, 0]}>
          <boxGeometry args={[1.9, 0.12, 1.9]} />
          {std(substrate)}
        </mesh>
        <mesh position={[0, 0.25, 0]}>
          <boxGeometry args={[1.2, 0.26, 1.2]} />
          {std(silicon)}
        </mesh>
      </group>
    )
  }
  if (shape === 'fau') {
    return (
      <group ref={group} position={position.toArray()} {...handlers} name={point.name}>
        <mesh>
          <boxGeometry args={[0.7, 0.32, 0.9]} />
          <meshPhysicalMaterial color={glass.color} transmission={glass.transmission} roughness={glass.roughness} ior={glass.ior} thickness={0.4} emissive={emissive} emissiveIntensity={lift} />
        </mesh>
        <mesh position={[0, 0.22, 0]}>
          <boxGeometry args={[0.7, 0.1, 0.9]} />
          {std(polymer)}
        </mesh>
      </group>
    )
  }
  if (shape === 'connector') {
    return (
      <group ref={group} position={position.toArray()} {...handlers} name={point.name}>
        {[-0.3, 0.3].map((dx) => (
          <mesh key={dx} position={[dx, 0, 0]}>
            <boxGeometry args={[0.55, 0.42, 0.42]} />
            {std(polymer)}
          </mesh>
        ))}
      </group>
    )
  }
  return (
    <group ref={group} position={position.toArray()} {...handlers} name={point.name}>
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.16, 0.16, 0.9, 24]} />
        <meshStandardMaterial color={fiber.color} transparent opacity={0.45} roughness={fiber.roughness} emissive={emissive} emissiveIntensity={lift} />
      </mesh>
    </group>
  )
}

/** Segment i (component i to i+1) carries the light after element i: its color is the API's
 * above_threshold flag for power_trace[i]; its pulse brightness is relative_power[i]. */
function Fiber({ trace, positions, palette }: { trace: TracePoint[]; positions: THREE.Vector3[]; palette: Palette }) {
  const still = useExplorer((s) => s.still)
  const invalidate = useThree((s) => s.invalidate)
  const good = palette.status.find((s) => s.key === 'NOT_EXCLUDED')?.color ?? '#0ca30c'
  const bad = palette.status.find((s) => s.key === 'EXCLUDED')?.color ?? '#d03b3b'
  const channel = palette.channels[0]?.color ?? '#3987e5'
  const curve = useMemo(() => new THREE.CatmullRomCurve3(positions, false, 'centripetal'), [positions])
  const n = positions.length - 1
  const segments = useMemo(
    () =>
      Array.from({ length: n }, (_, i) => {
        const samples = Array.from({ length: 25 }, (_, k) => curve.getPoint((i + k / 24) / n))
        return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(samples), 48, 0.07, 12, false)
      }),
    [curve, n],
  )
  useEffect(() => () => segments.forEach((g) => g.dispose()), [segments])
  const pulse = useRef<THREE.Mesh>(null)
  const material = useRef<THREE.MeshBasicMaterial>(null)
  useFrame(({ clock }) => {
    const mesh = pulse.current
    if (mesh === null || material.current === null) return
    const u = still ? 0.3 : (clock.elapsedTime / 3) % 1
    mesh.position.copy(curve.getPoint(u))
    const point = trace[Math.min(Math.floor(u * n), n - 1)]
    material.current.color.set(channel).multiplyScalar((point?.relative_power ?? 0) * PULSE_GAIN)
    if (!still) invalidate()
  })
  return (
    <group>
      {segments.map((geometry, i) => {
        const point = trace[i]
        if (point === undefined) return null
        const color = point.above_threshold ? good : bad
        return (
          <mesh key={i} geometry={geometry} raycast={() => null}>
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.45} roughness={0.3} />
          </mesh>
        )
      })}
      <mesh ref={pulse} raycast={() => null}>
        <sphereGeometry args={[0.12, 16, 12]} />
        <meshBasicMaterial ref={material} toneMapped={false} />
      </mesh>
    </group>
  )
}

function Laser({ report, start, palette }: { report: FeasibilityReport; start: THREE.Vector3; palette: Palette }) {
  const upstream = report.upstream
  if (upstream === null || upstream === undefined) return null
  const steel = palette.materials.find((m) => m.key === 'aluminium_dark') ?? palette.materials[0]!
  const at = new THREE.Vector3(start.x - SPACING * 1.4, 0, 0)
  const n = upstream.split_n
  const shown = Math.min(n, 24)
  const fanout = upstream.max_fanout
  return (
    <group name="laser">
      <mesh position={[at.x, 0.35, 0]}>
        <boxGeometry args={[1.1, 0.7, 1.0]} />
        <meshStandardMaterial color={steel.color} metalness={steel.metalness} roughness={steel.roughness} />
      </mesh>
      {Array.from({ length: shown }, (_, i) => {
        const z = (i - (shown - 1) / 2) * 0.14
        const end = i === 0 ? new THREE.Vector3(start.x - 0.9, FIBER_Y, 0) : new THREE.Vector3(start.x - 0.9, 0.2, z)
        const from = new THREE.Vector3(at.x + 0.55, 0.4, z * 0.3)
        const mid = from.clone().lerp(end, 0.5)
        const length = from.distanceTo(end)
        return (
          <group key={i}>
            <mesh position={mid} quaternion={new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), end.clone().sub(from).normalize())}>
              <cylinderGeometry args={[0.018, 0.018, length, 8]} />
              <meshBasicMaterial color={palette.cw} toneMapped={false} />
            </mesh>
            {i > 0 && (
              <mesh position={[end.x + 0.12, 0.2, end.z]}>
                <boxGeometry args={[0.24, 0.12, 0.1]} />
                <meshStandardMaterial color={steel.color} metalness={steel.metalness} roughness={steel.roughness} />
              </mesh>
            )}
          </group>
        )
      })}
      <Html position={[at.x, 1.05, 0]} center zIndexRange={[20, 10]}>
        <div className="leader-value" data-testid="fanout-label">
          laser 1:{n} split · max fan-out {fanout} {n > fanout ? '(beyond max)' : ''}
        </div>
      </Html>
    </group>
  )
}

export function LinkScene({ report, palette }: { report: FeasibilityReport; palette: Palette }) {
  const trace = report.power_trace
  const positions = useMemo(() => linkLayout(trace.length), [trace.length])
  const hovered = useExplorer((s) => s.hovered)
  const point = trace.find((p) => p.name === hovered)
  const index = point === undefined ? -1 : trace.indexOf(point)
  const input = point === undefined ? undefined : primaryInput(report, point)
  return (
    <group name="parts">
      {trace.map((p, i) => {
        const position = positions[i]
        return position === undefined ? null : <LinkComponent key={`${i}-${p.name}`} point={p} position={position} palette={palette} />
      })}
      <Fiber trace={trace} positions={positions} palette={palette} />
      {positions[0] && <Laser report={report} start={positions[0]} palette={palette} />}
      {point !== undefined && positions[index] !== undefined && (
        <Html position={positions[index]!.clone().add(new THREE.Vector3(0, 0.9, 0))} center zIndexRange={[50, 40]}>
          <div className="tooltip" role="tooltip">
            <strong>{displayName(report, point)}</strong>
            <div>
              {point.loss_db !== null
                ? `loss ${fmt(point.loss_db)} dB`
                : `${input?.path === 'tx.launch_oma_min' ? 'launch' : 'sensitivity'} ${input ? `${input.value} ${input.unit}` : ''}`}
            </div>
            <div>source: {input?.source_class ?? '—'}</div>
            <div>citation: {input?.citation_key ?? 'none'}</div>
          </div>
        </Html>
      )}
    </group>
  )
}
