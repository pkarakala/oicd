// Shared UI primitives. Every data color comes from the API palette (GET /display); badges always
// carry a text label, and status badges an icon, so nothing is told by color alone.

import * as RadixTooltip from '@radix-ui/react-tooltip'
import { Check, CircleMinus, OctagonX, TriangleAlert } from 'lucide-react'
import { type ComponentProps, type ReactNode, createContext, forwardRef, useContext } from 'react'
import type { Palette } from '../api/client'
import { classSwatch, dimsSwatch, statusSwatch } from '../lib/format'

export const PaletteContext = createContext<Palette | undefined>(undefined)
export const usePalette = () => useContext(PaletteContext)

export function Tip({ label, children, side = 'bottom' }: { label: ReactNode; children: ReactNode; side?: 'top' | 'bottom' | 'left' | 'right' }) {
  return (
    <RadixTooltip.Root>
      <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
      <RadixTooltip.Portal>
        <RadixTooltip.Content side={side} sideOffset={6} className="tip">
          {label}
        </RadixTooltip.Content>
      </RadixTooltip.Portal>
    </RadixTooltip.Root>
  )
}

type ButtonProps = ComponentProps<'button'> & { label: string; shortcut?: string; active?: boolean }

/** An icon button with an accessible name and a tooltip naming its shortcut. */
export const IconButton = forwardRef<HTMLButtonElement, ButtonProps>(function IconButton(
  { label, shortcut, active, className = '', children, ...rest },
  ref,
) {
  return (
    <Tip label={shortcut ? `${label} (${shortcut})` : label}>
      <button
        ref={ref}
        type="button"
        aria-label={label}
        aria-pressed={active === undefined ? undefined : active}
        className={`icon-btn ${active ? 'is-active' : ''} ${className}`}
        {...rest}
      >
        {children}
      </button>
    </Tip>
  )
})

function Chip({ color, label, title, testId }: { color?: string; label: string; title?: string; testId?: string }) {
  return (
    <span className="chip" title={title} data-testid={testId}>
      <span className="chip-dot" style={{ background: color ?? 'var(--muted)' }} aria-hidden />
      {label}
    </span>
  )
}

export function ClassBadge({ cls }: { cls: string }) {
  const palette = usePalette()
  const swatch = classSwatch(palette, cls)
  return <Chip color={swatch?.color} label={swatch?.label ?? cls} title={`Source class: ${swatch?.label ?? cls}`} />
}

export function DimsBadge({ cls }: { cls: string }) {
  const palette = usePalette()
  const swatch = dimsSwatch(palette, cls)
  return <Chip color={swatch?.color} label={swatch?.label ?? cls} title={`Dimension class: ${cls}`} testId="dims-badge" />
}

const ICONS: Record<string, typeof Check> = {
  check: Check,
  'alert-triangle': TriangleAlert,
  'x-octagon': OctagonX,
  'minus-circle': CircleMinus,
}

export function StatusBadge({ status, testId }: { status: string; testId?: string }) {
  const palette = usePalette()
  const swatch = statusSwatch(palette, status)
  const Icon = ICONS[swatch?.icon ?? 'minus-circle'] ?? CircleMinus
  return (
    <span className="status-badge" style={{ color: swatch?.color }} data-testid={testId} data-status={status}>
      <Icon size={13} strokeWidth={2.4} aria-hidden />
      <span className="status-text">{swatch?.label ?? status}</span>
    </span>
  )
}

/** A badge for a caption: a source class, a check status or a written note. */
export function CaptionBadge({ badge }: { badge: string }) {
  const palette = usePalette()
  if (palette?.status.some((s) => s.key === badge)) return <StatusBadge status={badge} />
  if (palette?.classes.some((c) => c.key === badge)) return <ClassBadge cls={badge} />
  return <Chip label="OICD note" />
}

export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="kbd">{children}</kbd>
}

export function Section({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="section">
      <header className="section-head">
        <h3>{title}</h3>
        {aside}
      </header>
      {children}
    </section>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>
}

export const INDEPENDENCE =
  'Independent reconstruction from public information. Not affiliated with or endorsed by Lightmatter. Product names belong to their owners.'
