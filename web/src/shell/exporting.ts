// Downloads: the API's JSON as returned, and a 2× PNG of the viewport in clean mode.

import { useExplorer } from '../state/store'
import { capture } from '../viewport/Viewport'

export function download(content: string | Blob, name: string, type = 'application/octet-stream') {
  const blob = typeof content === 'string' ? new Blob([content], { type }) : content
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))

export async function exportPng(name: string): Promise<void> {
  const store = useExplorer.getState()
  const wasClean = store.clean
  const canvas = capture.gl?.domElement
  if (canvas === undefined) return
  store.setFlag('clean', true)
  capture.setDpr?.(2)
  for (let i = 0; i < 6; i++) {
    capture.invalidate?.()
    await frame()
  }
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
  capture.setDpr?.(Math.min(window.devicePixelRatio || 1, 2))
  useExplorer.getState().setFlag('clean', wasClean)
  capture.invalidate?.()
  if (blob !== null) download(blob, `${name}.png`, 'image/png')
}
