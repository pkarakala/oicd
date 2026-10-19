// Cmd/Ctrl+K: every product scene, part, analysis, view and command in one searchable list.

import * as Dialog from '@radix-ui/react-dialog'
import { Command } from 'cmdk'
import type { SceneList, SceneView } from '../api/client'
import { LINK_SCENE } from '../api/hooks'
import { useExplorer } from '../state/store'
import { DOCK_TABS } from '../state/url'
import { TAB_LABELS } from './Dock'
import { exportPng } from './exporting'
import { enterScene } from './navigation'

export function CommandPalette({ scenes, view }: { scenes: SceneList | undefined; view: SceneView | undefined }) {
  const open = useExplorer((s) => s.paletteOpen)
  const setOpen = useExplorer((s) => s.setPaletteOpen)
  const run = (action: () => void) => {
    setOpen(false)
    window.setTimeout(action, 0)
  }
  const s = useExplorer.getState
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="palette" aria-describedby={undefined}>
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <Command label="Command palette" loop>
            <Command.Input placeholder="Go to a product, part, analysis or command…" className="palette-input" autoFocus />
            <Command.List className="palette-list">
              <Command.Empty className="palette-empty">Nothing matches.</Command.Empty>
              <Command.Group heading="Products and scenes">
                {(scenes?.info ?? []).map((i) => (
                  <Command.Item key={i.id} value={`scene ${i.name} ${i.id} ${i.breadcrumb}`} onSelect={() => run(() => enterScene(i.id))}>
                    {i.name}
                    <span className="palette-hint">{i.breadcrumb || i.level}</span>
                  </Command.Item>
                ))}
                <Command.Item value="scene link budget worked example" onSelect={() => run(() => enterScene(LINK_SCENE))}>
                  Link budget (worked example)
                  <span className="palette-hint">schematic</span>
                </Command.Item>
              </Command.Group>
              {view && (
                <Command.Group heading={`Parts in ${view.scene.scene.name}`}>
                  {view.scene.part.map((p) => (
                    <Command.Item
                      key={p.id}
                      value={`part ${p.name} ${p.id} ${p.assembly}`}
                      onSelect={() =>
                        run(() => {
                          s().select(p.id)
                          s().command({ kind: 'part', part: p.id })
                        })
                      }
                    >
                      {p.name}
                      <span className="palette-hint">{p.enters ? `↘ ${p.enters}` : p.dims_class}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              )}
              <Command.Group heading="Analyses">
                {DOCK_TABS.map((t) => (
                  <Command.Item key={t} value={`analysis ${TAB_LABELS[t]}`} onSelect={() => run(() => s().setDockTab(t))}>
                    {TAB_LABELS[t]}
                  </Command.Item>
                ))}
              </Command.Group>
              <Command.Group heading="Views">
                {(['front', 'top', 'right', 'iso'] as const).map((v, i) => (
                  <Command.Item key={v} value={`view ${v}`} onSelect={() => run(() => s().command({ kind: 'view', view: v }))}>
                    {v === 'iso' ? 'Isometric' : v[0]!.toUpperCase() + v.slice(1)} view
                    <span className="palette-hint">{i + 1}</span>
                  </Command.Item>
                ))}
                <Command.Item value="view fit all" onSelect={() => run(() => s().command({ kind: 'fit' }))}>
                  Fit all <span className="palette-hint">F</span>
                </Command.Item>
                <Command.Item value="view orthographic perspective projection" onSelect={() => run(() => s().setProjection(s().projection === 'perspective' ? 'orthographic' : 'perspective'))}>
                  Toggle orthographic <span className="palette-hint">O</span>
                </Command.Item>
              </Command.Group>
              <Command.Group heading="Commands">
                {(['x', 'y', 'z'] as const).map((a) => (
                  <Command.Item key={a} value={`command section ${a}`} onSelect={() => run(() => s().setSection(a))}>
                    Section {a.toUpperCase()}
                  </Command.Item>
                ))}
                <Command.Item value="command section off" onSelect={() => run(() => s().setSection(null))}>
                  Section off
                </Command.Item>
                <Command.Item value="command exploded view" onSelect={() => run(() => window.dispatchEvent(new CustomEvent('oicd:explode')))}>
                  Exploded view <span className="palette-hint">E</span>
                </Command.Item>
                <Command.Item value="command measure" onSelect={() => run(() => s().setMeasure(true))}>
                  Measure <span className="palette-hint">M</span>
                </Command.Item>
                <Command.Item value="command tour guided" onSelect={() => run(() => s().setTourStop(0))}>
                  Start the guided tour
                </Command.Item>
                <Command.Item value="command tint schematic" onSelect={() => run(() => s().setFlag('tint', !s().tint))}>
                  Tint SCHEMATIC parts <span className="palette-hint">T</span>
                </Command.Item>
                <Command.Item value="command theme dark light" onSelect={() => run(() => s().setTheme(s().theme === 'light' ? 'dark' : 'light'))}>
                  Toggle theme
                </Command.Item>
                <Command.Item value="command export png" onSelect={() => run(() => void exportPng(`oicd-${s().scene}`))}>
                  Export PNG at 2×
                </Command.Item>
                <Command.Item value="command undo" onSelect={() => run(() => s().undo())}>
                  Undo <span className="palette-hint">⌘Z</span>
                </Command.Item>
                <Command.Item value="command redo" onSelect={() => run(() => s().redo())}>
                  Redo <span className="palette-hint">⌘⇧Z</span>
                </Command.Item>
                <Command.Item value="command shortcuts keyboard" onSelect={() => run(() => s().setShortcutsOpen(true))}>
                  Keyboard shortcuts <span className="palette-hint">?</span>
                </Command.Item>
              </Command.Group>
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
