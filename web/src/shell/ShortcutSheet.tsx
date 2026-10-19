import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useExplorer } from '../state/store'
import { SHORTCUTS } from './shortcuts'
import { Kbd } from './ui'

export function ShortcutSheet() {
  const open = useExplorer((s) => s.shortcutsOpen)
  const setOpen = useExplorer((s) => s.setShortcutsOpen)
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog" aria-describedby={undefined}>
          <div className="dialog-head">
            <Dialog.Title className="dialog-title">Keyboard shortcuts</Dialog.Title>
            <Dialog.Close className="icon-btn" aria-label="Close">
              <X size={16} />
            </Dialog.Close>
          </div>
          <table className="shortcut-table">
            <tbody>
              {SHORTCUTS.map(([keys, action]) => (
                <tr key={keys}>
                  <td>
                    <Kbd>{keys}</Kbd>
                  </td>
                  <td>{action}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted small">
            Mouse: left drag orbits, right drag pans, the wheel zooms to the cursor; double-click a part to zoom into
            its level.
          </p>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
