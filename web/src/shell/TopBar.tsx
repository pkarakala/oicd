// Top bar: scene (product) switcher, zoom-level breadcrumb, view menu, tour, undo/redo, theme,
// export, command palette and shortcuts.

import * as Menu from '@radix-ui/react-dropdown-menu'
import {
  ChevronDown,
  ChevronRight,
  Command,
  Download,
  Keyboard,
  Moon,
  Navigation,
  Redo2,
  Sun,
  Undo2,
} from 'lucide-react'
import { useEffect } from 'react'
import { type FeasibilityReport, type SceneInfo, type SceneList, type SceneView, getJson } from '../api/client'
import { LINK_SCENE } from '../api/hooks'
import { useExplorer } from '../state/store'
import { enterScene } from './navigation'
import { download, exportPng } from './exporting'
import { IconButton } from './ui'

const GROUPS: { label: string; levels: SceneInfo['level'][] }[] = [
  { label: 'Rack (OICD reference design)', levels: ['rack'] },
  { label: 'Trays', levels: ['tray'] },
  { label: 'Packages and modules', levels: ['package'] },
  { label: 'Device level', levels: ['pic', 'device'] },
]

export function sceneInfos(scenes: SceneList | undefined): Map<string, SceneInfo> {
  return new Map((scenes?.info ?? []).map((i) => [i.id, i]))
}

/** The breadcrumb chain from the top scene down to `scene`. */
export function chainOf(infos: Map<string, SceneInfo>, scene: string): SceneInfo[] {
  const out: SceneInfo[] = []
  let current = infos.get(scene)
  const seen = new Set<string>()
  while (current !== undefined && !seen.has(current.id)) {
    out.unshift(current)
    seen.add(current.id)
    current = current.parent ? infos.get(current.parent) : undefined
  }
  return out
}

function SceneMenu({ scenes }: { scenes: SceneList | undefined }) {
  const scene = useExplorer((s) => s.scene)
  const infos = sceneInfos(scenes)
  const current = scene === LINK_SCENE ? 'Link budget (worked example)' : (infos.get(scene)?.name ?? scene)
  const groups = GROUPS.map((g) => ({ ...g, items: [...infos.values()].filter((i) => g.levels.includes(i.level)) })).filter(
    (g) => g.items.length > 0,
  )
  return (
    <Menu.Root>
      <Menu.Trigger className="menu-trigger scene-trigger" aria-label="Choose a product or scene" data-testid="scene-menu">
        <span className="scene-name">{current}</span>
        <ChevronDown size={14} aria-hidden />
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="menu" sideOffset={6} align="start">
          {groups.map((g) => (
            <Menu.Group key={g.label}>
              <Menu.Label className="menu-label">{g.label}</Menu.Label>
              {g.items.map((i) => (
                <Menu.Item key={i.id} className="menu-item" onSelect={() => enterScene(i.id)} data-testid={`scene-${i.id}`}>
                  <span>{i.name}</span>
                  <span className="menu-hint">{i.unit === 'um' ? 'µm' : i.unit}</span>
                </Menu.Item>
              ))}
            </Menu.Group>
          ))}
          <Menu.Separator className="menu-sep" />
          <Menu.Item className="menu-item" onSelect={() => enterScene(LINK_SCENE)} data-testid="scene-link">
            <span>Link budget (worked example)</span>
            <span className="menu-hint">schematic</span>
          </Menu.Item>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}

function Breadcrumb({ scenes }: { scenes: SceneList | undefined }) {
  const scene = useExplorer((s) => s.scene)
  const chain = scene === LINK_SCENE ? [] : chainOf(sceneInfos(scenes), scene)
  return (
    <nav className="breadcrumb" aria-label="Zoom level" data-testid="breadcrumb">
      {scene === LINK_SCENE && <span className="crumb is-current">Link budget</span>}
      {chain.map((info, i) => {
        const last = i === chain.length - 1
        return (
          <span key={info.id} className="crumb-wrap">
            {i > 0 && <ChevronRight size={13} className="crumb-sep" aria-hidden />}
            <button
              type="button"
              className={`crumb ${last ? 'is-current' : ''}`}
              aria-current={last ? 'page' : undefined}
              onClick={() => !last && enterScene(info.id)}
            >
              {info.breadcrumb || info.name}
            </button>
          </span>
        )
      })}
    </nav>
  )
}

function ViewMenu() {
  const s = useExplorer()
  const check = (on: boolean) => (on ? '✓' : '')
  const item = (label: string, onSelect: () => void, hint = '') => (
    <Menu.Item className="menu-item" onSelect={onSelect}>
      <span>{label}</span>
      <span className="menu-hint">{hint}</span>
    </Menu.Item>
  )
  return (
    <Menu.Root>
      <Menu.Trigger className="menu-trigger" aria-label="View menu">
        View <ChevronDown size={14} aria-hidden />
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="menu" sideOffset={6} align="start">
          <Menu.Label className="menu-label">Camera</Menu.Label>
          {item('Front', () => s.command({ kind: 'view', view: 'front' }), '1')}
          {item('Top', () => s.command({ kind: 'view', view: 'top' }), '2')}
          {item('Right', () => s.command({ kind: 'view', view: 'right' }), '3')}
          {item('Isometric', () => s.command({ kind: 'view', view: 'iso' }), '4')}
          {item('Fit all', () => s.command({ kind: 'fit' }), 'F')}
          {item('Fit selection', () => s.command({ kind: 'fitSelection' }), '⇧F')}
          {item(`Orthographic ${check(s.projection === 'orthographic')}`, () =>
            s.setProjection(s.projection === 'perspective' ? 'orthographic' : 'perspective'), 'O')}
          <Menu.Separator className="menu-sep" />
          <Menu.Label className="menu-label">Tools</Menu.Label>
          {(['x', 'y', 'z'] as const).map((a) => item(`Section ${a.toUpperCase()} ${check(s.sectionAxis === a)}`, () => s.setSection(s.sectionAxis === a ? null : a)))}
          {item(`Exploded view ${check(s.explode > 0)}`, () => window.dispatchEvent(new CustomEvent('oicd:explode')), 'E')}
          {item(`Measure ${check(s.measure)}`, () => s.setMeasure(!s.measure), 'M')}
          <Menu.Separator className="menu-sep" />
          <Menu.Label className="menu-label">Display</Menu.Label>
          {item(`Labels ${check(s.labels)}`, () => s.setFlag('labels', !s.labels), 'L')}
          {item(`Physics overlays ${check(s.overlays)}`, () => s.setFlag('overlays', !s.overlays), 'V')}
          {item(`Tint SCHEMATIC parts ${check(s.tint)}`, () => s.setFlag('tint', !s.tint), 'T')}
          {item(`Pulses paused ${check(s.still)}`, () => s.setFlag('still', !s.still), 'P')}
          {item(`Clean mode ${check(s.clean)}`, () => s.setFlag('clean', !s.clean))}
          {item('Show all parts', () => s.showAll())}
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}

function ExportMenu({ view, report }: { view: SceneView | undefined; report: FeasibilityReport | undefined }) {
  const scene = useExplorer((s) => s.scene)
  const theme = useExplorer((s) => s.theme)
  const product = view?.scene.scene.product ?? ''
  return (
    <Menu.Root>
      <Menu.Trigger className="menu-trigger" aria-label="Export" data-testid="export-menu">
        <Download size={14} aria-hidden /> Export
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="menu" sideOffset={6} align="end">
          <Menu.Item
            className="menu-item"
            disabled={report === undefined}
            onSelect={() => report && download(JSON.stringify(report, null, 2), 'oicd-feasibility-report.json', 'application/json')}
            data-testid="export-report"
          >
            Link report JSON (POST /evaluate)
          </Menu.Item>
          <Menu.Item
            className="menu-item"
            disabled={product === ''}
            onSelect={async () => {
              const data = await getJson<unknown>(`/catalog/${encodeURIComponent(product)}`)
              download(JSON.stringify(data, null, 2), `oicd-${product}.json`, 'application/json')
            }}
          >
            Architecture twin JSON (GET /catalog/{product || '…'})
          </Menu.Item>
          <Menu.Item
            className="menu-item"
            disabled={scene === LINK_SCENE}
            onSelect={async () => {
              const data = await getJson<unknown>(`/overlay/${encodeURIComponent(scene)}?mode=${theme}`)
              download(JSON.stringify({ scene: view, overlay: data }, null, 2), `oicd-scene-${scene}.json`, 'application/json')
            }}
          >
            Scene and overlay JSON
          </Menu.Item>
          <Menu.Separator className="menu-sep" />
          <Menu.Item className="menu-item" onSelect={() => void exportPng(`oicd-${scene}`)} data-testid="export-png">
            PNG at 2× (clean)
          </Menu.Item>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}

export function TopBar({ scenes, view, report }: { scenes: SceneList | undefined; view: SceneView | undefined; report: FeasibilityReport | undefined }) {
  const theme = useExplorer((s) => s.theme)
  const setTheme = useExplorer((s) => s.setTheme)
  const canUndo = useExplorer((s) => s.past.length > 0)
  const canRedo = useExplorer((s) => s.future.length > 0)
  const undo = useExplorer((s) => s.undo)
  const redo = useExplorer((s) => s.redo)
  const setPaletteOpen = useExplorer((s) => s.setPaletteOpen)
  const setShortcutsOpen = useExplorer((s) => s.setShortcutsOpen)
  const tourStop = useExplorer((s) => s.tourStop)
  const setTourStop = useExplorer((s) => s.setTourStop)
  const scene = useExplorer((s) => s.scene)
  const captions = view?.captions.length ?? 0

  // zoom in / out from the keyboard; tour steps clamped to this scene's stops
  useEffect(() => {
    const onZoom = (e: Event) => {
      const s = useExplorer.getState()
      if ((e as CustomEvent<string>).detail === 'in') {
        const part = view?.scene.part.find((p) => p.id === s.selection)
        if (part?.enters) enterScene(part.enters, part.id)
      } else {
        const parent = view?.scene.scene.parent
        if (parent) enterScene(parent)
      }
    }
    const onTour = (e: Event) => {
      const s = useExplorer.getState()
      if (s.tourStop === null) return
      const next = s.tourStop + (e as CustomEvent<number>).detail
      if (next >= 0 && next < captions) s.setTourStop(next)
    }
    window.addEventListener('oicd:zoom', onZoom)
    window.addEventListener('oicd:tour', onTour)
    return () => {
      window.removeEventListener('oicd:zoom', onZoom)
      window.removeEventListener('oicd:tour', onTour)
    }
  }, [view, captions])

  return (
    <header className="topbar">
      <div className="brand" aria-label="OICD">
        <span className="brand-mark" aria-hidden>
          ◇
        </span>
        <span className="brand-name">OICD</span>
        <span className="brand-sub">twin explorer</span>
      </div>
      <SceneMenu scenes={scenes} />
      <Breadcrumb scenes={scenes} />
      <div className="topbar-spacer" />
      <ViewMenu />
      {scene !== LINK_SCENE && captions > 0 && (
        <button
          type="button"
          className={`menu-trigger ${tourStop !== null ? 'is-active' : ''}`}
          onClick={() => setTourStop(tourStop === null ? 0 : null)}
          aria-pressed={tourStop !== null}
          data-testid="tour-button"
        >
          <Navigation size={14} aria-hidden /> Tour
        </button>
      )}
      <IconButton label="Undo" shortcut="⌘Z" disabled={!canUndo} onClick={undo}>
        <Undo2 size={16} />
      </IconButton>
      <IconButton label="Redo" shortcut="⌘⇧Z" disabled={!canRedo} onClick={redo}>
        <Redo2 size={16} />
      </IconButton>
      <IconButton
        label={theme === 'light' ? 'Dark theme' : 'Light theme'}
        onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        data-testid="theme-toggle"
      >
        {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
      </IconButton>
      <ExportMenu view={view} report={report} />
      <IconButton label="Command palette" shortcut="⌘K" onClick={() => setPaletteOpen(true)} data-testid="palette-button">
        <Command size={16} />
      </IconButton>
      <IconButton label="Keyboard shortcuts" shortcut="?" onClick={() => setShortcutsOpen(true)}>
        <Keyboard size={16} />
      </IconButton>
    </header>
  )
}
