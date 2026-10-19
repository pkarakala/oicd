// Scene geometry from the API, mapped to three.js. The TOML frame is x width, y depth (front at
// −y), z up; three.js is Y-up, so (x, y, z) → (x, z, −y). Sizes and positions are never changed.

import * as THREE from 'three'
import type { Part } from '../api/client'

export type Vec3 = [number, number, number]

export function toThree([x, y, z]: readonly number[]): THREE.Vector3 {
  return new THREE.Vector3(x ?? 0, z ?? 0, -(y ?? 0))
}

export function fromThree(v: THREE.Vector3): Vec3 {
  return [v.x, -v.z, v.y]
}

const AXIS_X = new THREE.Vector3(1, 0, 0)
const AXIS_Y = new THREE.Vector3(0, 0, -1) // TOML y in three.js
const AXIS_Z = new THREE.Vector3(0, 1, 0) // TOML z in three.js
const DEG = Math.PI / 180

/** TOML rotation_deg (intrinsic x, then y, then z, about the TOML axes) as a quaternion. */
export function rotationOf(part: Part): THREE.Quaternion {
  const [rx, ry, rz] = part.rotation_deg
  return new THREE.Quaternion()
    .setFromAxisAngle(AXIS_X, rx * DEG)
    .multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Y, ry * DEG))
    .multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Z, rz * DEG))
}

/** TOML offsets of every instance: index i walks x first, then y, then z of the grid. */
export function instanceOffsets(part: Part): Vec3[] {
  const [nx, ny] = part.grid
  const [px, py, pz] = part.pitch
  return Array.from({ length: part.count }, (_, i) => {
    const ix = i % nx
    const iy = Math.floor(i / nx) % ny
    const iz = Math.floor(i / (nx * ny))
    return [ix * px, iy * py, iz * pz] as Vec3
  })
}

/** Instance centers in TOML coordinates, with the explode vector scaled by t (0 to 1). */
export function instanceCenters(part: Part, explode = 0): Vec3[] {
  const [x, y, z] = part.position
  const [ex, ey, ez] = part.explode
  return instanceOffsets(part).map(([dx, dy, dz]) => [x + dx + ex * explode, y + dy + ey * explode, z + dz + ez * explode])
}

/** The part's shape at the origin, in three.js axes. Tubes follow their path relative to the
 * part position; rings revolve a rectangular wall profile about TOML z. */
export function partGeometry(part: Part): THREE.BufferGeometry {
  const [sx, sy, sz] = part.size
  switch (part.shape) {
    case 'box':
      return new THREE.BoxGeometry(sx, sz, sy)
    case 'cylinder': {
      const g = new THREE.CylinderGeometry(sx / 2, sx / 2, sz, 20, 1)
      if (sy !== sx) g.scale(1, 1, sy / sx)
      return g
    }
    case 'sphere': {
      const g = new THREE.SphereGeometry(sx / 2, 16, 16)
      if (sy !== sx || sz !== sx) g.scale(1, sz / sx, sy / sx)
      return g
    }
    case 'ring': {
      const outer = sx / 2
      const inner = outer - (part.wall ?? sx / 10)
      const h = sz / 2
      const profile = [
        new THREE.Vector2(inner, -h),
        new THREE.Vector2(outer, -h),
        new THREE.Vector2(outer, h),
        new THREE.Vector2(inner, h),
        new THREE.Vector2(inner, -h),
      ]
      return new THREE.LatheGeometry(profile, 160)
    }
    case 'tube': {
      const curve = tubeCurve(part)
      const segments = Math.max(48, 48 * (part.path.length - 1))
      return new THREE.TubeGeometry(curve, segments, sx / 2, 16, false)
    }
  }
}

/** The centerline of a tube, relative to the part position, in three.js axes. */
export function tubeCurve(part: Part): THREE.Curve<THREE.Vector3> {
  const points = part.path.map((p) => toThree(p))
  if (points.length === 2) return new THREE.LineCurve3(points[0]!, points[1]!)
  return new THREE.CatmullRomCurve3(points, false, 'centripetal')
}

/** A light path's centerline for one instance, in world (three.js) coordinates. */
export function centerline(part: Part, center: Vec3): THREE.Curve<THREE.Vector3> {
  const origin = toThree(center)
  if (part.shape === 'tube') {
    const points = part.path.map((p) => toThree(p).add(origin))
    if (points.length === 2) return new THREE.LineCurve3(points[0]!, points[1]!)
    return new THREE.CatmullRomCurve3(points, false, 'centripetal')
  }
  // cylinders: along their own axis (TOML z before rotation), first point at −L/2
  const half = part.size[2] / 2
  const q = rotationOf(part)
  const a = new THREE.Vector3(0, -half, 0).applyQuaternion(q).add(origin)
  const b = new THREE.Vector3(0, half, 0).applyQuaternion(q).add(origin)
  return new THREE.LineCurve3(a, b)
}

/** World (three.js) bounds of a part's instances, rotation and explode included. */
export function partBounds(part: Part, explode = 0): THREE.Box3 {
  const box = new THREE.Box3()
  const q = rotationOf(part)
  const [sx, sy, sz] = part.size
  for (const c of instanceCenters(part, explode)) {
    const origin = toThree(c)
    if (part.shape === 'tube') {
      const r = new THREE.Vector3(sx / 2, sx / 2, sx / 2)
      for (const p of part.path) {
        const point = toThree(p).add(origin)
        box.expandByPoint(point.clone().add(r))
        box.expandByPoint(point.sub(r))
      }
      continue
    }
    for (const dx of [-sx / 2, sx / 2])
      for (const dy of [-sz / 2, sz / 2])
        for (const dz of [-sy / 2, sy / 2]) box.expandByPoint(new THREE.Vector3(dx, dy, dz).applyQuaternion(q).add(origin))
  }
  return box
}

export function sceneBounds(parts: readonly Part[], explode = 0): THREE.Box3 {
  const box = new THREE.Box3()
  for (const part of parts) box.union(partBounds(part, explode))
  if (box.isEmpty()) box.set(new THREE.Vector3(-1, -1, -1), new THREE.Vector3(1, 1, 1))
  return box
}

export function distance(a: Vec3, b: Vec3): number {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])
}
