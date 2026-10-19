// The explorer shell: top bar, model tree, viewport, Inspector and the bottom dock, with the
// command palette, shortcut sheet and footer. State lives in the store; data comes from the API.

import { useEffect, useState } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { API_URL } from '../api/client'
import { LINK_SCENE, useDisplay, useEvaluate, useOverlay, useProfile, useScene, useSceneList } from '../api/hooks'
import { useExplorer, urlState } from '../state/store'
import { encodeUrl } from '../state/url'
import { Viewport } from '../viewport/Viewport'
import { CommandPalette } from './CommandPalette'
import { Dock } from './Dock'
import { Footer } from './Footer'
import { Inspector } from './Inspector'
import { ModelTree } from './ModelTree'
import { ShortcutSheet } from './ShortcutSheet'
import { TopBar } from './TopBar'
import { enterScene } from './navigation'
import { useShortcuts } from './shortcuts'
import { PaletteContext } from './ui'

function useUrlSync() {
  useEffect(
    () =>
      useExplorer.subscribe((s) => {
        const search = encodeUrl(urlState(s))
        if (search !== window.location.search) {
          window.history.replaceState(null, '', `${window.location.pathname}${search}`)
        }
      }),
    [],
  )
}

function useSceneEvents() {
  useEffect(() => {
    const onEnter = (e: Event) => {
      const { part, scene } = (e as CustomEvent<{ part: string; scene: string }>).detail
      enterScene(scene, part)
    }
    let frame = 0
    const onExplode = () => {
      cancelAnimationFrame(frame)
      const from = useExplorer.getState().explode
      const to = from > 0 ? 0 : 1
      const start = performance.now()
      const step = (now: number) => {
        const t = Math.min((now - start) / 650, 1)
        const eased = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2
        useExplorer.getState().setExplode(from + (to - from) * eased)
        if (t < 1) frame = requestAnimationFrame(step)
      }
      frame = requestAnimationFrame(step)
    }
    window.addEventListener('oicd:enter', onEnter)
    window.addEventListener('oicd:explode', onExplode)
    return () => {
      window.removeEventListener('oicd:enter', onEnter)
      window.removeEventListener('oicd:explode', onExplode)
      cancelAnimationFrame(frame)
    }
  }, [])
}

export default function App() {
  const theme = useExplorer((s) => s.theme)
  const scene = useExplorer((s) => s.scene)
  const overlayCase = useExplorer((s) => s.overlayCase)
  const isolationDb = useExplorer((s) => s.isolationDb)
  const tourStop = useExplorer((s) => s.tourStop)
  const link = useExplorer((s) => s.design.link)
  const loadLink = useExplorer((s) => s.loadLink)
  const display = useDisplay(theme)
  const palette = display.data
  const profile = useProfile('worked_example')
  const evaluation = useEvaluate(link)
  const view = useScene(scene)
  const overlay = useOverlay(scene, theme, overlayCase, isolationDb)
  const scenes = useSceneList()
  const [booted, setBooted] = useState(false)

  useUrlSync()
  useSceneEvents()
  useShortcuts()

  useEffect(() => {
    if (profile.data && useExplorer.getState().design.link === null) loadLink(profile.data)
  }, [profile.data, loadLink])

  // tour stops: select the stop's part and fly to it
  useEffect(() => {
    if (tourStop === null || view.data === undefined) return
    const caption = view.data.captions[tourStop]
    if (caption === undefined) return
    const s = useExplorer.getState()
    s.select(caption.part)
    s.command({ kind: 'part', part: caption.part })
  }, [tourStop, view.data])

  useEffect(() => {
    if (palette === undefined) return
    const root = document.documentElement
    root.dataset.theme = theme
    root.style.setProperty('--surface', palette.surface)
    root.style.setProperty('--ink', palette.ink)
    root.style.setProperty('--muted', palette.muted)
    root.style.setProperty('--grid', palette.grid)
    setBooted(true)
  }, [palette, theme])

  if (palette === undefined) {
    return (
      <div className="boot" role={display.isError ? 'alert' : 'status'}>
        {display.isError ? `The engine API at ${API_URL} is unreachable: ${String(display.error)}` : 'Loading the engine palette…'}
      </div>
    )
  }

  const report = evaluation.data
  const error = evaluation.error ?? view.error ?? overlay.error ?? scenes.error
  return (
    <PaletteContext.Provider value={palette}>
      <div className={`app ${booted ? 'is-booted' : ''}`}>
        <TopBar scenes={scenes.data} view={view.data} report={report} />
        {error && (
          <div className="error-banner" role="alert">
            Engine rejected the input or is unreachable: {error instanceof Error ? error.message : String(error)}
          </div>
        )}
        <Group orientation="vertical" className="workspace">
          <Panel id="pane-main" defaultSize="70%" minSize="25%">
            <Group orientation="horizontal" className="workspace-row">
              <Panel id="pane-tree" defaultSize={250} minSize={170} collapsible collapsedSize={0} className="pane">
                <ModelTree view={scene === LINK_SCENE ? undefined : view.data} report={scene === LINK_SCENE ? report : undefined} />
              </Panel>
              <Separator className="sep sep-v" />
              <Panel id="pane-viewport" minSize="30%" className="pane pane-viewport">
                <Viewport palette={palette} view={view.data} overlay={overlay.data} report={report} />
              </Panel>
              <Separator className="sep sep-v" />
              <Panel id="pane-inspector" defaultSize={350} minSize={250} collapsible collapsedSize={0} className="pane">
                <Inspector view={scene === LINK_SCENE ? undefined : view.data} overlay={overlay.data} report={report} />
              </Panel>
            </Group>
          </Panel>
          <Separator className="sep sep-h" />
          <Panel id="pane-dock" defaultSize="30%" minSize={140} collapsible collapsedSize={34} className="pane">
            <Dock view={view.data} report={report} pending={evaluation.isFetching} />
          </Panel>
        </Group>
        <Footer />
        <CommandPalette scenes={scenes.data} view={view.data} />
        <ShortcutSheet />
      </div>
    </PaletteContext.Provider>
  )
}
