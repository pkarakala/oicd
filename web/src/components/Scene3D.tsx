import { CameraControls, Grid } from '@react-three/drei'
import { Canvas, type ThreeEvent } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState } from 'react'
import * as THREE from 'three'
import { displayName, fmt, primaryInput } from '../format'
import type { FeasibilityReport, TracePoint } from '../types'

// Schematic layout constants (scene units, not physical dimensions).
const SPACING = 2.4
const FIBER_Y = 0.55
const MAX_EMISSIVE = 1.6

export type CameraPreset = 'overview' | 'tx' | 'rx'

type Shape = 'engine' | 'fau' | 'connector' | 'fiber' | 'generic'

function shapeOf(point: TracePoint): Shape {
  if (point.kind === 'reference_plane') return 'engine'
  if (/FAU/i.test(point.name)) return 'fau'
  if (/connector|patch/i.test(point.name)) return 'connector'
  if (/SMF|fiber|fibre/i.test(point.name)) return 'fiber'
  return 'generic'
}

function layout(count: number): THREE.Vector3[] {
  return Array.from({ length: count }, (_, i) => {
    const edge = i === 0 || i === count - 1
    return new THREE.Vector3((i - (count - 1) / 2) * SPACING, FIBER_Y, edge ? 0 : 0.6 * Math.sin(i * 1.7))
  })
}

/** Color for a headroom value returned by the API: green at or above threshold, red below. */
function headroomColor(headroomDb: number): THREE.Color {
  const strength = Math.min(Math.abs(headroomDb) / 3, 1)
  return new THREE.Color().setHSL(headroomDb >= 0 ? 0.33 : 0.0, 0.85, 0.62 - 0.27 * strength)
}

interface ComponentProps {
  point: TracePoint
  position: THREE.Vector3
  highlighted: boolean
  selected: boolean
  onHover: (hovering: boolean) => void
  onSelect: () => void
}

function LinkComponent({ point, position, highlighted, selected, onHover, onSelect }: ComponentProps) {
  const shape = shapeOf(point)
  const emissiveIntensity = (point.loss_fraction ?? 0) * MAX_EMISSIVE + (highlighted ? 0.35 : 0)
  const emissive = selected ? '#60a5fa' : highlighted ? '#fbbf24' : '#ff7a1a'
  const handlers = {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation()
      onHover(true)
    },
    onPointerOut: () => onHover(false),
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation()
      onSelect()
    },
  }
  const accent = (
    <meshStandardMaterial color="#9aa4b2" metalness={0.5} roughness={0.35} emissive={emissive} emissiveIntensity={emissiveIntensity} />
  )

  if (shape === 'engine') {
    // Optical engine: package on a substrate, with the PIC die on top.
    return (
      <group position={[position.x, 0, position.z]} {...handlers}>
        <mesh position={[0, 0.06, 0]}>
          <boxGeometry args={[1.9, 0.12, 1.9]} />
          <meshStandardMaterial color="#1f5f3a" roughness={0.8} emissive={emissive} emissiveIntensity={highlighted || selected ? 0.25 : 0} />
        </mesh>
        <mesh position={[0, 0.25, 0]}>
          <boxGeometry args={[1.2, 0.26, 1.2]} />
          <meshStandardMaterial color="#2b2f36" metalness={0.3} roughness={0.5} />
        </mesh>
        <mesh position={[0, 0.42, 0]}>
          <boxGeometry args={[0.7, 0.08, 0.7]} />
          <meshStandardMaterial color="#6d7c99" metalness={0.8} roughness={0.2} />
        </mesh>
      </group>
    )
  }
  if (shape === 'fau') {
    // Fiber-array unit: glass V-groove block under a lid.
    return (
      <group position={position.toArray()} {...handlers}>
        <mesh>
          <boxGeometry args={[0.7, 0.32, 0.9]} />
          <meshPhysicalMaterial color="#bfe3ff" transmission={0.6} roughness={0.1} thickness={0.4} emissive={emissive} emissiveIntensity={emissiveIntensity} />
        </mesh>
        <mesh position={[0, 0.22, 0]}>
          <boxGeometry args={[0.7, 0.1, 0.9]} />
          {accent}
        </mesh>
      </group>
    )
  }
  if (shape === 'connector') {
    // Mated connector pair along the fiber axis.
    return (
      <group position={position.toArray()} {...handlers}>
        {[-0.3, 0.3].map((dx) => (
          <mesh key={dx} position={[dx, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
            <boxGeometry args={[0.42, 0.55, 0.42]} />
            {accent}
          </mesh>
        ))}
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.1, 0.1, 0.3, 24]} />
          <meshStandardMaterial color="#e5e7eb" emissive={emissive} emissiveIntensity={emissiveIntensity} />
        </mesh>
      </group>
    )
  }
  if (shape === 'fiber') {
    // Fiber segment: a translucent sleeve around the tube.
    return (
      <group position={position.toArray()} {...handlers}>
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.16, 0.16, 0.9, 24]} />
          <meshStandardMaterial color="#facc15" transparent opacity={0.45} emissive={emissive} emissiveIntensity={emissiveIntensity} />
        </mesh>
      </group>
    )
  }
  return (
    <mesh position={position.toArray()} {...handlers}>
      <boxGeometry args={[0.5, 0.5, 0.5]} />
      {accent}
    </mesh>
  )
}

/** One smooth curve through all components; segment i (component i to i+1) carries the power
 * after element i, so it takes power_trace[i].headroom_db's color. */
function FiberTube({ trace, positions }: { trace: TracePoint[]; positions: THREE.Vector3[] }) {
  const segments = useMemo(() => {
    if (positions.length < 2) return []
    const curve = new THREE.CatmullRomCurve3(positions, false, 'centripetal')
    const n = positions.length - 1
    return Array.from({ length: n }, (_, i) => {
      const samples = Array.from({ length: 25 }, (_, k) => curve.getPoint((i + k / 24) / n))
      return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(samples), 48, 0.07, 12, false)
    })
  }, [positions])
  useEffect(() => () => segments.forEach((g) => g.dispose()), [segments])
  return (
    <group>
      {segments.map((geometry, i) => {
        const point = trace[i]
        if (point === undefined) return null
        const color = headroomColor(point.headroom_db)
        return (
          <mesh key={i} geometry={geometry}>
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.45} roughness={0.3} />
          </mesh>
        )
      })}
    </group>
  )
}

function CameraRig({ preset, positions }: { preset: CameraPreset; positions: THREE.Vector3[] }) {
  const controls = useRef<CameraControls>(null)
  const first = positions[0]
  const last = positions[positions.length - 1]
  const span = positions.length * SPACING
  useEffect(() => {
    const c = controls.current
    if (c === null || first === undefined || last === undefined) return
    if (preset === 'overview') void c.setLookAt(0, span * 0.36, span * 0.6, 0, -0.6, 0, true)
    if (preset === 'tx') void c.setLookAt(first.x + 1.5, 2.4, 3.6, first.x + 1.0, 0.3, 0, true)
    if (preset === 'rx') void c.setLookAt(last.x - 1.5, 2.4, 3.6, last.x - 1.0, 0.3, 0, true)
  }, [preset, first, last, span])
  return <CameraControls ref={controls} makeDefault minDistance={1.5} maxDistance={60} />
}

interface SceneProps {
  report: FeasibilityReport
  hovered: number | null
  selected: number | null
  preset: CameraPreset
  onHover: (index: number | null) => void
  onSelect: (index: number | null) => void
}

export function Scene3D({ report, hovered, selected, preset, onHover, onSelect }: SceneProps) {
  const trace = report.power_trace
  const count = trace.length
  const positions = useMemo(() => layout(count), [count])
  const hoveredPoint = hovered === null ? undefined : trace[hovered]
  const hoveredInput = hoveredPoint === undefined ? undefined : primaryInput(report, hoveredPoint)
  const excluded = report.verdict === 'EXCLUDED'
  // Pointer position inside the scene, for placing the DOM tooltip next to the cursor.
  const [pointer, setPointer] = useState<{ x: number; y: number } | null>(null)

  return (
    <div
      className="scene-canvas"
      onPointerMove={(e) => {
        const box = e.currentTarget.getBoundingClientRect()
        setPointer({ x: e.clientX - box.left, y: e.clientY - box.top })
      }}
      onPointerLeave={() => setPointer(null)}
    >
      <Canvas
        camera={{ position: [0, 6, 9], fov: 45 }}
        dpr={[1, 2]}
        gl={{ preserveDrawingBuffer: true }}
        onPointerMissed={() => onSelect(null)}
      >
        <color attach="background" args={['#0b1020']} />
        <hemisphereLight args={['#dbeafe', '#1e293b', 0.7]} />
        <directionalLight position={[6, 10, 6]} intensity={1.6} />
        <directionalLight position={[-6, 4, -4]} intensity={0.5} />
        <CameraRig preset={preset} positions={positions} />
        <Grid args={[60, 60]} position={[0, -0.001, 0]} cellColor="#1e293b" sectionColor="#334155" fadeDistance={45} infiniteGrid />

        {trace.map((point, i) => {
          const position = positions[i]
          if (position === undefined) return null
          return (
            <LinkComponent
              key={`${i}-${point.name}`}
              point={point}
              position={position}
              highlighted={hovered === i}
              selected={selected === i}
              onHover={(on) => onHover(on ? i : null)}
              onSelect={() => onSelect(i)}
            />
          )
        })}
        <FiberTube trace={trace} positions={positions} />
      </Canvas>

      <div className={`badge ${excluded ? 'badge-excluded' : 'badge-ok'}`} aria-live="polite">
        <div className="badge-verdict">{report.verdict}</div>
        <div className="badge-margin">margin {fmt(report.margin_db)} dB</div>
      </div>

      {hoveredPoint !== undefined && pointer !== null && (
        <div className="tooltip" role="tooltip" style={{ left: pointer.x + 14, top: pointer.y + 14 }}>
          <strong>{displayName(report, hoveredPoint)}</strong>
          <div>
            {hoveredPoint.loss_db !== null
              ? `loss ${fmt(hoveredPoint.loss_db)} dB`
              : `${hoveredInput?.path === 'tx.launch_oma_min' ? 'launch' : 'sensitivity'} ${hoveredInput ? `${hoveredInput.value} ${hoveredInput.unit}` : ''}`}
          </div>
          <div>source: {hoveredInput?.source_class ?? '—'}</div>
          <div>citation: {hoveredInput?.citation_key ?? 'none'}</div>
        </div>
      )}
    </div>
  )
}
