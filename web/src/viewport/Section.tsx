// Section view: one clipping plane across X, Y or Z (TOML axes), moved by a drag gizmo or the
// slider; cut solids get stencil caps drawn with a 45° hatch.

import { TransformControls } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import { type RefObject, useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import type { Palette } from '../api/client'
import { useExplorer } from '../state/store'
import type { Axis } from '../state/url'
import { CLIP_PLANES, hatchTexture } from './materials'

// TOML x → three x (cut away +x), TOML y (depth) → three −z (cut away the front, +z),
// TOML z (height) → three y (cut away the top).
const NORMALS: Record<Axis, THREE.Vector3> = {
  x: new THREE.Vector3(-1, 0, 0),
  y: new THREE.Vector3(0, 0, -1),
  z: new THREE.Vector3(0, -1, 0),
}
const THREE_AXIS: Record<Axis, 'x' | 'y' | 'z'> = { x: 'x', y: 'z', z: 'y' }

export function sectionPosition(bounds: THREE.Box3, axis: Axis, offset: number): THREE.Vector3 {
  const center = bounds.getCenter(new THREE.Vector3())
  const size = bounds.getSize(new THREE.Vector3())
  const k = THREE_AXIS[axis]
  // offset is a fraction of the extent along the axis, positive toward the cut-away side
  center[k] += offset * size[k]
  return center
}

export function Section({ bounds, palette }: { bounds: THREE.Box3; palette: Palette }) {
  const axis = useExplorer((s) => s.sectionAxis)
  const offset = useExplorer((s) => s.sectionOffset)
  const setOffset = useExplorer((s) => s.setSectionOffset)
  const clean = useExplorer((s) => s.clean)
  const gl = useThree((s) => s.gl)
  const invalidate = useThree((s) => s.invalidate)
  const plane = useMemo(() => new THREE.Plane(), [])
  const handle = useRef<THREE.Object3D>(null)
  const hatch = useMemo(() => hatchTexture(palette.muted, palette.surface), [palette.muted, palette.surface])
  useEffect(() => () => hatch.dispose(), [hatch])
  const size = bounds.getSize(new THREE.Vector3())
  const span = Math.max(size.x, size.y, size.z)

  useEffect(() => {
    gl.localClippingEnabled = true
    CLIP_PLANES.length = 0
    if (axis !== null) {
      const at = sectionPosition(bounds, axis, offset)
      plane.normal.copy(NORMALS[axis])
      plane.constant = -plane.normal.dot(at)
      CLIP_PLANES.push(plane)
    }
    invalidate()
    return () => {
      CLIP_PLANES.length = 0
    }
  }, [axis, offset, bounds, plane, gl, invalidate])

  if (axis === null) return null
  const at = sectionPosition(bounds, axis, offset)
  const normal = NORMALS[axis]
  const quaternion = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal.clone().negate())
  hatch.repeat.set(30, 30)
  return (
    <group name="section">
      <mesh position={at} quaternion={quaternion} renderOrder={2} raycast={() => null}>
        <planeGeometry args={[span * 3, span * 3]} />
        <meshBasicMaterial
          map={hatch}
          side={THREE.DoubleSide}
          stencilWrite
          stencilRef={0}
          stencilFunc={THREE.NotEqualStencilFunc}
          stencilFail={THREE.ReplaceStencilOp}
          stencilZFail={THREE.ReplaceStencilOp}
          stencilZPass={THREE.ReplaceStencilOp}
          polygonOffset
          polygonOffsetFactor={-1}
        />
      </mesh>
      <object3D ref={handle} position={at} />
      {!clean && (
        <TransformControls
          object={handle as RefObject<THREE.Object3D>}
          mode="translate"
          showX={THREE_AXIS[axis] === 'x'}
          showY={THREE_AXIS[axis] === 'y'}
          showZ={THREE_AXIS[axis] === 'z'}
          size={0.7}
          onObjectChange={() => {
            const object = handle.current
            if (object === null) return
            const k = THREE_AXIS[axis]
            const center = bounds.getCenter(new THREE.Vector3())
            setOffset((object.position[k] - center[k]) / Math.max(size[k], 1e-9))
          }}
        />
      )}
    </group>
  )
}
