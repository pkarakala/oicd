// Camera: damped orbit, pan and zoom to cursor (camera-controls), perspective or orthographic,
// standard views (1 front, 2 top, 3 right, 4 iso), fit all (F) and fit selection (Shift+F).

import { CameraControls, OrthographicCamera, PerspectiveCamera } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { type CameraCommand, type ViewName, useExplorer } from '../state/store'
import type { Projection } from '../state/url'
import { partObjects } from './Parts'

export const FOV = 32
const ISO_POLAR = Math.atan(Math.SQRT2) // 54.7°: the isometric elevation
const VIEWS: Record<ViewName, [number, number]> = {
  front: [0, Math.PI / 2],
  top: [0, 1e-4],
  right: [Math.PI / 2, Math.PI / 2],
  iso: [Math.PI / 4, ISO_POLAR],
}

// The last camera state, carried across a perspective/orthographic switch.
const carried = { position: new THREE.Vector3(), target: new THREE.Vector3(), valid: false }

// Only our two cameras are driven; R3F's initial default camera is replaced on the first render.
const MANAGED = 'oicd-camera'
const managed = (camera: THREE.Camera) => camera.name === MANAGED

function sphereOf(box: THREE.Box3): THREE.Sphere {
  return box.getBoundingSphere(new THREE.Sphere())
}

function objectBox(id: string): THREE.Box3 | null {
  const object = partObjects.get(id)
  if (object === undefined) return null
  const box = new THREE.Box3().setFromObject(object)
  return box.isEmpty() ? null : box
}

export function Cameras({ projection, bounds }: { projection: Projection; bounds: THREE.Box3 }) {
  const radius = sphereOf(bounds).radius
  return (
    <>
      <PerspectiveCamera
        name={MANAGED}
        makeDefault={projection === 'perspective'}
        fov={FOV}
        near={radius / 2000}
        far={radius * 400}
        position={[radius * 2, radius * 1.6, radius * 2]}
      />
      <OrthographicCamera
        name={MANAGED}
        makeDefault={projection === 'orthographic'}
        near={-radius * 200}
        far={radius * 400}
        position={[radius * 2, radius * 1.6, radius * 2]}
      />
    </>
  )
}

export function CameraRig({ bounds, sceneKey }: { bounds: THREE.Box3; sceneKey: string }) {
  const controls = useRef<CameraControls>(null)
  const camera = useThree((s) => s.camera)
  const size = useThree((s) => s.size)
  const invalidate = useThree((s) => s.invalidate)
  const command = useExplorer((s) => s.camera)
  const scene = useExplorer((s) => s.scene)
  const selection = useExplorer((s) => s.selection)
  const handled = useRef(-1)

  // distance limits follow the scene's size (each zoom level is its own scene and unit)
  useEffect(() => {
    const c = controls.current
    if (c === null) return
    const radius = sphereOf(bounds).radius
    c.minDistance = radius / 400
    c.maxDistance = radius * 60
    c.minZoom = 0.001
    c.maxZoom = 1e6
  }, [bounds, camera])

  // a new camera (projection switch): continue from where the last one was
  useEffect(() => {
    const c = controls.current
    if (c === null || !carried.valid || !managed(camera)) return
    const { position, target } = carried
    const distance = position.distanceTo(target)
    if (camera instanceof THREE.OrthographicCamera) {
      const visible = 2 * distance * Math.tan(THREE.MathUtils.degToRad(FOV / 2))
      void c.setLookAt(position.x, position.y, position.z, target.x, target.y, target.z, false)
      void c.zoomTo(size.height / visible, false)
    } else if (camera instanceof THREE.PerspectiveCamera) {
      void c.setLookAt(position.x, position.y, position.z, target.x, target.y, target.z, false)
    }
    invalidate()
  }, [camera])

  useEffect(() => {
    const c = controls.current
    if (c === null || command === null || command.nonce === handled.current) return
    if (sceneKey !== scene || !managed(camera)) return // wait for the geometry and our camera
    handled.current = command.nonce
    run(c, command.command, bounds, selection)
    invalidate()
  }, [command, sceneKey, scene, bounds, selection, invalidate, camera])

  return (
    <CameraControls
      ref={controls}
      makeDefault
      smoothTime={0.22}
      draggingSmoothTime={0.06}
      dollyToCursor
      onChange={() => {
        const c = controls.current
        if (c === null || !managed(c.camera)) return
        c.getPosition(carried.position)
        c.getTarget(carried.target)
        carried.valid = true
        window.dispatchEvent(new Event('oicd:camera'))
      }}
    />
  )
}

// a little air around the scene, so the overlay panel and labels do not crowd it
const FIT_MARGIN = 1.12

function run(c: CameraControls, command: CameraCommand, bounds: THREE.Box3, selection: string | null) {
  const all = sphereOf(bounds)
  all.radius *= FIT_MARGIN
  switch (command.kind) {
    case 'fit':
      void c.fitToSphere(all, true)
      return
    case 'view': {
      const [azimuth, polar] = VIEWS[command.view]
      void c.rotateTo(azimuth, polar, true)
      void c.fitToSphere(all, true)
      return
    }
    case 'fitSelection':
    case 'part': {
      const id = command.kind === 'part' ? command.part : selection
      const box = id === null ? null : objectBox(id)
      void c.fitToSphere(box === null ? all : sphereOf(box), true)
      return
    }
  }
}
