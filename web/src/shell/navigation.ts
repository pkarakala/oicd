// Semantic zoom between scenes: fly to the part, fade, then open the scene in its own unit.

import { useExplorer } from '../state/store'

export function enterScene(target: string, part?: string) {
  const store = useExplorer.getState()
  if (target === store.scene) return
  document.body.classList.add('is-transitioning')
  if (part !== undefined) store.command({ kind: 'part', part })
  window.setTimeout(
    () => {
      useExplorer.getState().setScene(target)
      window.setTimeout(() => document.body.classList.remove('is-transitioning'), 260)
    },
    part === undefined ? 120 : 420,
  )
}
