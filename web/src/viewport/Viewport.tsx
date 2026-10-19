// The CAD viewport: demand-driven canvas, studio rendering, parts or the schematic link scene,
// physics overlays, section, measure, labels, ViewCube, and the DOM overlays (scale bar, color
// bar, cases, tour) around it. Every number shown comes from the API.

import { Bvh, GizmoHelper, GizmoViewcube, StatsGl } from '@react-three/drei'
import { Canvas, useThree } from '@react-three/fiber'
import { useCallback, useEffect, useMemo, useState } from 'react'
import * as THREE from 'three'
import type { FeasibilityReport, Overlay, Palette, SceneView } from '../api/client'
import { LINK_SCENE } from '../api/hooks'
import { formatLength, niceStep } from '../lib/format'
import { sceneBounds } from '../lib/geometry'
import { useExplorer } from '../state/store'
import { CameraRig, Cameras, FOV } from './CameraRig'
import { Effects } from './Effects'
import { type Anchor, LabelLayer, Projector, type Projected, gridAnchors, partAnchors } from './Labels'
import { LightPaths } from './LightPaths'
import { LinkScene, linkBounds } from './LinkScene'
import { Measure } from './Measure'
import { Parts, partObjects } from './Parts'
import { Section } from './Section'
import { Background, Floor, StudioLights } from './Studio'
import { ViewportOverlays } from './ViewportOverlays'

export const capture: {
  gl: THREE.WebGLRenderer | null
  setDpr: ((dpr: number) => void) | null
  invalidate: (() => void) | null
} = { gl: null, setDpr: null, invalidate: null }

function Probes({ onScale, bounds }: { onScale: (worldPerPixel: number) => void; bounds: THREE.Box3 }) {
  const camera = useThree((s) => s.camera)
  const size = useThree((s) => s.size)
  const gl = useThree((s) => s.gl)
  const setDpr = useThree((s) => s.setDpr)
  const invalidate = useThree((s) => s.invalidate)
  const controls = useThree((s) => s.controls) as unknown as { getTarget?: (v: THREE.Vector3) => THREE.Vector3 } | null
  useEffect(() => {
    capture.gl = gl
    capture.setDpr = setDpr
    capture.invalidate = () => invalidate()
  }, [gl, setDpr, invalidate])
  useEffect(() => {
    let frame = 0
    const update = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        if (camera instanceof THREE.OrthographicCamera) {
          onScale((camera.top - camera.bottom) / camera.zoom / Math.max(size.height, 1))
        } else if (camera instanceof THREE.PerspectiveCamera) {
          const target = controls?.getTarget?.(new THREE.Vector3()) ?? bounds.getCenter(new THREE.Vector3())
          const d = camera.position.distanceTo(target)
          onScale((2 * d * Math.tan(THREE.MathUtils.degToRad(FOV / 2))) / Math.max(size.height, 1))
        }
      })
    }
    update()
    window.addEventListener('oicd:camera', update)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('oicd:camera', update)
    }
  }, [camera, size.height, controls, onScale, bounds])
  // test and export hooks: screen position of a part's bounding-box corner
  useEffect(() => {
    const hooks = {
      camera() {
        return { name: camera.name, type: camera.type, position: camera.position.toArray(), near: camera.near, far: camera.far }
      },
      corner(part: string, signs: [number, number, number]): { x: number; y: number } | null {
        const object = partObjects.get(part)
        if (object === undefined) return null
        const box = new THREE.Box3().setFromObject(object)
        const p = new THREE.Vector3(
          signs[0] < 0 ? box.min.x : box.max.x,
          signs[2] < 0 ? box.min.y : box.max.y,
          signs[1] < 0 ? box.max.z : box.min.z, // TOML −y (front) is three +z
        ).project(camera)
        const rect = gl.domElement.getBoundingClientRect()
        return { x: rect.left + ((p.x + 1) / 2) * rect.width, y: rect.top + ((1 - p.y) / 2) * rect.height }
      },
    }
    ;(window as unknown as { __oicd?: typeof hooks }).__oicd = hooks
  }, [camera, gl])
  return null
}

interface ViewportProps {
  palette: Palette
  view: SceneView | undefined
  overlay: Overlay | undefined
  report: FeasibilityReport | undefined
}

export function Viewport({ palette, view, overlay, report }: ViewportProps) {
  const scene = useExplorer((s) => s.scene)
  const projection = useExplorer((s) => s.projection)
  const explode = useExplorer((s) => s.explode)
  const labels = useExplorer((s) => s.labels)
  const overlays = useExplorer((s) => s.overlays)
  const clean = useExplorer((s) => s.clean)
  const still = useExplorer((s) => s.still)
  const measure = useExplorer((s) => s.measure)
  const select = useExplorer((s) => s.select)
  const command = useExplorer((s) => s.command)
  const [worldPerPixel, setWorldPerPixel] = useState(1)
  const [projected, setProjected] = useState<Map<string, Projected>>(new Map())
  const onProject = useCallback((p: Map<string, Projected>) => setProjected(p), [])
  const hidden = useExplorer((s) => s.hidden)
  const isolated = useExplorer((s) => s.isolated)
  // "settled": no camera change for a moment (tests and screenshots wait on it)
  const [settled, setSettled] = useState(false)
  useEffect(() => {
    let timer = window.setTimeout(() => setSettled(true), 900)
    const moved = () => {
      setSettled(false)
      window.clearTimeout(timer)
      timer = window.setTimeout(() => setSettled(true), 700)
    }
    window.addEventListener('oicd:camera', moved)
    return () => {
      window.clearTimeout(timer)
      window.removeEventListener('oicd:camera', moved)
    }
  }, [])

  const isLink = scene === LINK_SCENE
  const loaded = isLink ? report !== undefined : view !== undefined && view.scene.scene.id === scene
  const sceneKey = loaded ? scene : ''
  const unit = isLink ? 'mm' : (view?.scene.scene.unit ?? 'mm')
  const parts = useMemo(() => (view ? view.scene.part : []), [view])
  const bounds = useMemo(() => (isLink ? linkBounds(report) : sceneBounds(parts)), [isLink, report, parts])
  const radius = bounds.getBoundingSphere(new THREE.Sphere()).radius
  const floorBounds = useMemo(() => (isLink ? bounds : sceneBounds(parts, explode)), [isLink, bounds, parts, explode])

  const anchors = useMemo<Anchor[]>(() => {
    if (!loaded || clean) return []
    const out = labels && !isLink ? partAnchors(parts, overlay, { explode, hidden, isolated, overlays }) : []
    return labels && !isLink ? [...out, ...gridAnchors(floorBounds, unit)] : out
  }, [loaded, clean, labels, isLink, parts, overlay, explode, hidden, isolated, overlays, floorBounds, unit])
  // a newly loaded scene starts from the isometric view
  useEffect(() => {
    if (sceneKey) command({ kind: 'view', view: 'iso' })
  }, [sceneKey, command])

  return (
    <div className="viewport" data-testid="viewport" data-scene={sceneKey || 'loading'} data-settled={settled && sceneKey !== '' ? 'true' : 'false'}>
      <Canvas
        frameloop="demand"
        dpr={[1, 2]}
        flat
        gl={{ antialias: false, stencil: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' }}
        onPointerMissed={() => {
          if (!measure) select(null)
        }}
        aria-label="3D viewport"
      >
        <Cameras projection={projection} bounds={bounds} />
        <CameraRig bounds={bounds} sceneKey={sceneKey} />
        <Background palette={palette} />
        <StudioLights radius={radius} />
        <group name="content">
          <Bvh firstHitOnly>
            {isLink && report && <LinkScene report={report} palette={palette} />}
            {!isLink && view && <Parts view={view} overlay={overlay} palette={palette} />}
          </Bvh>
          {!isLink && view && overlay && overlays && <LightPaths overlay={overlay} parts={parts} />}
        </group>
        {loaded && <Floor bounds={floorBounds} palette={palette} shadowsKey={`${scene}:${explode}`} />}
        <Projector anchors={anchors} onProject={onProject} />
        {!isLink && loaded && <Section bounds={bounds} palette={palette} />}
        <Measure unit={unit} radius={radius} ink={palette.ink} />
        <Probes onScale={setWorldPerPixel} bounds={bounds} />
        <Effects ink={palette.ink} sceneKey={sceneKey} />
        {!clean && (
          <GizmoHelper alignment="top-right" margin={[72, 72]} renderPriority={2}>
            <GizmoViewcube color={palette.surface} hoverColor={palette.grid} textColor={palette.ink} strokeColor={palette.muted} opacity={0.95} />
          </GizmoHelper>
        )}
        {import.meta.env.DEV && !clean && !still && <StatsGl className="fps-meter" />}
      </Canvas>
      <LabelLayer anchors={anchors} positions={projected} palette={palette} />
      <ViewportOverlays
        palette={palette}
        view={view}
        overlay={overlay}
        report={report}
        isLink={isLink}
        scaleBar={scaleBar(worldPerPixel, unit)}
      />
    </div>
  )
}

function scaleBar(worldPerPixel: number, unit: SceneView['scene']['scene']['unit']) {
  const length = niceStep(worldPerPixel * 140)
  return { px: length / worldPerPixel, label: formatLength(length, unit, 3) }
}
