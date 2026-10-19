// Studio look: procedural environment from Lightformers (no downloaded HDRI), a key and fill
// light, a neutral gradient background, soft contact shadows and an infinite grid with labels.

import { ContactShadows, Environment, Grid, Lightformer } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import { useEffect } from 'react'
import * as THREE from 'three'
import type { Palette } from '../api/client'
import { niceStep } from '../lib/format'

function gradient(top: string, bottom: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 4
  canvas.height = 256
  const ctx = canvas.getContext('2d')
  if (ctx !== null) {
    const g = ctx.createLinearGradient(0, 0, 0, 256)
    g.addColorStop(0, top)
    g.addColorStop(1, bottom)
    ctx.fillStyle = g
    ctx.fillRect(0, 0, 4, 256)
  }
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

export function Background({ palette }: { palette: Palette }) {
  const scene = useThree((s) => s.scene)
  const invalidate = useThree((s) => s.invalidate)
  useEffect(() => {
    const texture = gradient(palette.background_top, palette.background_bottom)
    scene.background = texture
    invalidate()
    return () => texture.dispose()
  }, [palette.background_top, palette.background_bottom, scene, invalidate])
  return null
}

export function StudioLights({ radius }: { radius: number }) {
  return (
    <>
      <Environment resolution={256} frames={1}>
        <Lightformer form="rect" intensity={2.2} position={[0, 6, 0]} rotation-x={Math.PI / 2} scale={[12, 12, 1]} />
        <Lightformer form="rect" intensity={1.4} position={[-6, 2, 4]} rotation-y={Math.PI / 3} scale={[8, 3, 1]} />
        <Lightformer form="rect" intensity={1.0} position={[6, 1, -4]} rotation-y={-Math.PI / 3} scale={[8, 3, 1]} />
        <Lightformer form="ring" intensity={0.6} position={[0, 2, -8]} scale={4} />
      </Environment>
      <ambientLight intensity={0.12} />
      <directionalLight position={[radius * 1.2, radius * 2.2, radius * 1.6]} intensity={1.1} />
      <directionalLight position={[-radius * 1.5, radius * 0.8, -radius]} intensity={0.35} />
    </>
  )
}

export function Floor({ bounds, palette, shadowsKey }: { bounds: THREE.Box3; palette: Palette; shadowsKey: string }) {
  const size = bounds.getSize(new THREE.Vector3())
  const center = bounds.getCenter(new THREE.Vector3())
  const span = Math.max(size.x, size.z, size.y * 0.5)
  const section = niceStep(span / 4)
  const cell = section / 10
  const floorY = bounds.min.y - span * 0.002
  return (
    <group>
      <Grid
        position={[0, floorY, 0]}
        infiniteGrid
        cellSize={cell}
        sectionSize={section}
        cellThickness={0.6}
        sectionThickness={1.1}
        cellColor={palette.grid}
        sectionColor={palette.muted}
        fadeDistance={span * 6}
        fadeStrength={1.6}
      />
      <ContactShadows
        key={shadowsKey}
        position={[center.x, floorY + span * 0.0005, center.z]}
        scale={span * 2.2}
        far={Math.max(size.y, span * 0.05)}
        blur={2.4}
        opacity={0.32}
        resolution={512}
        frames={1}
        color="#000000"
      />
    </group>
  )
}
