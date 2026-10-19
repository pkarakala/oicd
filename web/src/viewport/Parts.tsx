// Scene parts from GET /geometry/{scene}: one InstancedMesh per part (repeated parts are
// instances), merged feature edges (25°), PBR materials from the API, section stencil passes.

import { type ThreeEvent, useThree } from '@react-three/fiber'
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import type { Material, Overlay, Palette, Part, SceneView } from '../api/client'
import { instanceCenters, partGeometry, rotationOf, toThree } from '../lib/geometry'
import { useExplorer } from '../state/store'
import { type Look, isSolid, makeEdgeMaterial, makeMaterial, stencilMaterials } from './materials'

/** Part id → its scene object, for outlines, fitting and the measure tool. */
export const partObjects = new Map<string, THREE.Object3D>()

export const EDGE_THRESHOLD_DEG = 25

export function instanceMatrices(part: Part): THREE.Matrix4[] {
  const q = rotationOf(part)
  const one = new THREE.Vector3(1, 1, 1)
  return instanceCenters(part, 0).map((c) => new THREE.Matrix4().compose(toThree(c), q, one))
}

function mergedEdges(geometry: THREE.BufferGeometry, matrices: THREE.Matrix4[]): THREE.BufferGeometry {
  const edges = new THREE.EdgesGeometry(geometry, EDGE_THRESHOLD_DEG)
  const src = edges.getAttribute('position') as THREE.BufferAttribute
  const out = new Float32Array(src.count * 3 * matrices.length)
  const v = new THREE.Vector3()
  matrices.forEach((m, k) => {
    for (let i = 0; i < src.count; i++) {
      v.fromBufferAttribute(src, i).applyMatrix4(m)
      const o = (k * src.count + i) * 3
      out[o] = v.x
      out[o + 1] = v.y
      out[o + 2] = v.z
    }
  })
  edges.dispose()
  const merged = new THREE.BufferGeometry()
  merged.setAttribute('position', new THREE.BufferAttribute(out, 3))
  return merged
}

interface InstancesProps {
  geometry: THREE.BufferGeometry
  material: THREE.Material
  matrices: THREE.Matrix4[]
  renderOrder?: number
  pickable?: boolean
  name?: string
  handlers?: Partial<{
    onPointerOver: (e: ThreeEvent<PointerEvent>) => void
    onPointerOut: (e: ThreeEvent<PointerEvent>) => void
    onClick: (e: ThreeEvent<MouseEvent>) => void
    onDoubleClick: (e: ThreeEvent<MouseEvent>) => void
  }>
}

function Instances({ geometry, material, matrices, renderOrder = 0, pickable = false, name, handlers }: InstancesProps) {
  const ref = useRef<THREE.InstancedMesh>(null)
  const invalidate = useThree((s) => s.invalidate)
  useLayoutEffect(() => {
    const mesh = ref.current
    if (mesh === null) return
    matrices.forEach((m, i) => mesh.setMatrixAt(i, m))
    mesh.instanceMatrix.needsUpdate = true
    mesh.computeBoundingSphere()
    mesh.computeBoundingBox()
    invalidate()
  }, [matrices, invalidate])
  return (
    <instancedMesh
      ref={ref}
      name={name}
      args={[geometry, undefined, matrices.length]}
      material={material}
      renderOrder={renderOrder}
      frustumCulled={false}
      raycast={pickable ? THREE.InstancedMesh.prototype.raycast : () => null}
      {...handlers}
    />
  )
}

interface PartObjectProps {
  part: Part
  material: Material
  look: Look
  edgeColor: string
  hoverColor: string
  explode: number
  sectionOn: boolean
}

function PartObject({ part, material, look, edgeColor, hoverColor, explode, sectionOn }: PartObjectProps) {
  const geometry = useMemo(() => partGeometry(part), [part])
  const matrices = useMemo(() => instanceMatrices(part), [part])
  const edges = useMemo(() => mergedEdges(geometry, matrices), [geometry, matrices])
  const thickness = Math.min(...part.size)
  const mat = useMemo(
    () => makeMaterial(material, look, thickness),
    [material, look.color, look.emissive, look.emissiveIntensity, look.opacity, thickness],
  )
  const edgeMat = useMemo(() => makeEdgeMaterial(edgeColor, material.opacity < 1 ? 0.7 : 1), [edgeColor, material.opacity])
  const stencil = useMemo(() => stencilMaterials(), [])
  const group = useRef<THREE.Group>(null)
  const invalidate = useThree((s) => s.invalidate)
  const hovered = useExplorer((s) => s.hovered === part.id)
  const measure = useExplorer((s) => s.measure)
  const hover = useExplorer((s) => s.hover)
  const select = useExplorer((s) => s.select)

  useEffect(() => () => geometry.dispose(), [geometry])
  useEffect(() => () => edges.dispose(), [edges])
  useEffect(() => () => mat.dispose(), [mat])
  useEffect(() => () => edgeMat.dispose(), [edgeMat])

  useEffect(() => {
    const object = group.current
    if (object === null) return
    partObjects.set(part.id, object)
    return () => {
      if (partObjects.get(part.id) === object) partObjects.delete(part.id)
    }
  }, [part.id])

  // hover: a light emissive lift on top of any overlay glow
  useEffect(() => {
    mat.emissive.set(hovered ? hoverColor : (look.emissive ?? '#000000'))
    mat.emissiveIntensity = hovered ? Math.max(0.18, look.emissiveIntensity ?? 0) : (look.emissiveIntensity ?? 0)
    invalidate()
  }, [hovered, hoverColor, mat, look.emissive, look.emissiveIntensity, invalidate])

  const handlers = {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation()
      hover(part.id)
    },
    onPointerOut: () => hover(null),
    onClick: (e: ThreeEvent<MouseEvent>) => {
      if (measure) return // the measure tool handles picks
      e.stopPropagation()
      select(part.id)
    },
    onDoubleClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation()
      if (part.enters) window.dispatchEvent(new CustomEvent('oicd:enter', { detail: { part: part.id, scene: part.enters } }))
    },
  }
  const offset = toThree(part.explode).multiplyScalar(explode)
  return (
    <group ref={group} position={offset} userData={{ part: part.id }}>
      <Instances geometry={geometry} material={mat} matrices={matrices} pickable name={part.id} handlers={handlers} />
      {sectionOn && isSolid(material) && (
        <>
          <Instances geometry={geometry} material={stencil[0]} matrices={matrices} renderOrder={1} />
          <Instances geometry={geometry} material={stencil[1]} matrices={matrices} renderOrder={1} />
        </>
      )}
      <lineSegments geometry={edges} material={edgeMat} raycast={() => null} />
    </group>
  )
}

export function Parts({ view, overlay, palette }: { view: SceneView; overlay: Overlay | undefined; palette: Palette }) {
  const hidden = useExplorer((s) => s.hidden)
  const isolated = useExplorer((s) => s.isolated)
  const explode = useExplorer((s) => s.explode)
  const tint = useExplorer((s) => s.tint)
  const overlays = useExplorer((s) => s.overlays)
  const sectionOn = useExplorer((s) => s.sectionAxis !== null)
  const materials = useMemo(() => new Map(palette.materials.map((m) => [m.key, m])), [palette])
  const values = useMemo(() => new Map((overlay?.values ?? []).map((v) => [v.part, v])), [overlay])
  const carriers = useMemo(() => new Set((overlay?.paths ?? []).map((p) => p.part)), [overlay])
  const fallback = palette.materials[0]!
  return (
    <group name="parts">
      {view.scene.part.map((part) => {
        if (hidden.includes(part.id) || (isolated !== null && isolated !== part.id)) return null
        const material = materials.get(part.material) ?? fallback
        const value = overlays ? values.get(part.id) : undefined
        const look: Look = {}
        if (tint && part.dims_class === 'SCHEMATIC') look.color = palette.schematic_tint
        if (value?.color) look.color = value.color
        if (overlays && carriers.has(part.id)) look.opacity = 0.32
        if (value?.intensity !== undefined && value.intensity !== null) {
          look.emissive = material.color
          look.emissiveIntensity = 0.4 + 2.2 * value.intensity
        }
        return (
          <PartObject
            key={`${view.scene.scene.id}:${part.id}`}
            part={part}
            material={material}
            look={look}
            edgeColor={material.edge}
            hoverColor={palette.muted}
            explode={explode}
            sectionOn={sectionOn}
          />
        )
      })}
    </group>
  )
}
