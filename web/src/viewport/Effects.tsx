// Post-processing: N8AO ambient occlusion, selection outline, bloom only above luminance 1 (light
// paths are the only HDR emitters), AgX tone mapping and SMAA.

import { Bloom, EffectComposer, N8AO, Outline, SMAA, ToneMapping } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { useEffect, useState } from 'react'
import type * as THREE from 'three'
import { useExplorer } from '../state/store'
import { partObjects } from './Parts'

export function Effects({ ink, sceneKey }: { ink: string; sceneKey: string }) {
  const selection = useExplorer((s) => s.selection)
  const clean = useExplorer((s) => s.clean)
  const [selected, setSelected] = useState<THREE.Object3D[]>([])
  useEffect(() => {
    // the selected part's object exists once its scene has rendered
    const id = window.setTimeout(() => {
      const object = selection === null ? undefined : partObjects.get(selection)
      setSelected(object === undefined || clean ? [] : [object])
    }, 0)
    return () => window.clearTimeout(id)
  }, [selection, sceneKey, clean])
  return (
    <EffectComposer multisampling={0} stencilBuffer renderPriority={1}>
      <N8AO halfRes screenSpaceRadius aoRadius={28} distanceFalloff={0.6} intensity={2.2} quality="medium" />
      <Outline
        selection={selected}
        visibleEdgeColor={ink}
        hiddenEdgeColor={ink}
        edgeStrength={4}
        blur={false}
        xRay
      />
      <Bloom luminanceThreshold={1} luminanceSmoothing={0.15} intensity={0.9} mipmapBlur />
      <ToneMapping mode={ToneMappingMode.AGX} />
      <SMAA />
    </EffectComposer>
  )
}
