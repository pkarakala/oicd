// three.js materials built from the API's PBR materials (GET /display). Colors are the API's;
// the only choices made here are rendering ones (side, depth writes, clipping).

import * as THREE from 'three'
import type { Material } from '../api/client'

/** Clipping planes shared by every part material; the section tool mutates this array. */
export const CLIP_PLANES: THREE.Plane[] = []

export interface Look {
  color?: string // overrides the material color (SCHEMATIC tint, margin colormap)
  emissive?: string
  emissiveIntensity?: number
  opacity?: number // light carriers turn translucent so the light paths inside them show
}

export function makeMaterial(m: Material, look: Look, thickness: number): THREE.MeshStandardMaterial {
  const params = {
    color: new THREE.Color(look.color ?? m.color),
    metalness: m.metalness,
    roughness: m.roughness,
    emissive: new THREE.Color(look.emissive ?? '#000000'),
    emissiveIntensity: look.emissiveIntensity ?? 0,
    clippingPlanes: CLIP_PLANES,
    clipShadows: true,
  }
  const material =
    m.transmission > 0
      ? new THREE.MeshPhysicalMaterial({
          ...params,
          transmission: m.transmission,
          ior: m.ior,
          thickness,
          transparent: true,
        })
      : new THREE.MeshStandardMaterial(params)
  const opacity = Math.min(m.opacity, look.opacity ?? 1)
  if (opacity < 1) {
    material.transparent = true
    material.opacity = opacity
    material.depthWrite = false
    material.side = THREE.DoubleSide
  }
  return material
}

export function makeEdgeMaterial(color: string, opacity = 1): THREE.LineBasicMaterial {
  return new THREE.LineBasicMaterial({
    color: new THREE.Color(color),
    transparent: opacity < 1,
    opacity,
    clippingPlanes: CLIP_PLANES,
  })
}

/** True for parts that are cut solids under the section tool (they get stencil caps). */
export function isSolid(m: Material): boolean {
  return m.opacity >= 1 && m.transmission === 0
}

// Stencil passes for section caps: back faces add, front faces subtract; where the count is not
// zero the cap plane is inside a cut solid.
export function stencilMaterials(): [THREE.MeshBasicMaterial, THREE.MeshBasicMaterial] {
  const base = {
    depthWrite: false,
    depthTest: false,
    colorWrite: false,
    stencilWrite: true,
    stencilFunc: THREE.AlwaysStencilFunc,
    clippingPlanes: CLIP_PLANES,
  }
  const back = new THREE.MeshBasicMaterial({
    ...base,
    side: THREE.BackSide,
    stencilFail: THREE.IncrementWrapStencilOp,
    stencilZFail: THREE.IncrementWrapStencilOp,
    stencilZPass: THREE.IncrementWrapStencilOp,
  })
  const front = new THREE.MeshBasicMaterial({
    ...base,
    side: THREE.FrontSide,
    stencilFail: THREE.DecrementWrapStencilOp,
    stencilZFail: THREE.DecrementWrapStencilOp,
    stencilZPass: THREE.DecrementWrapStencilOp,
  })
  return [back, front]
}

/** A 45° hatch for section caps, drawn once. */
export function hatchTexture(ink: string, paper: string): THREE.CanvasTexture {
  const size = 64
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size
  const ctx = canvas.getContext('2d')
  if (ctx !== null) {
    ctx.fillStyle = paper
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = ink
    ctx.lineWidth = 3
    for (let k = -size; k <= size * 2; k += 16) {
      ctx.beginPath()
      ctx.moveTo(k, 0)
      ctx.lineTo(k - size, size)
      ctx.stroke()
    }
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}
