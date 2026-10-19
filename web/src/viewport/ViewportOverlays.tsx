// DOM overlays around the canvas: tool bar, scene caption, scale bar, margin color bar with the
// legend, reference-plane cases and diplexer isolation, the tour bar and the link verdict badge.

import * as Slider from '@radix-ui/react-slider'
import * as ToggleGroup from '@radix-ui/react-toggle-group'
import { useState } from 'react'
import {
  Box,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Expand,
  Grid3x3,
  Layers,
  Lightbulb,
  Maximize,
  Pause,
  Play,
  Ruler,
  Scissors,
  SquareDashed,
  Tags,
  X,
} from 'lucide-react'
import type { FeasibilityReport, Overlay, Palette, SceneView } from '../api/client'
import { fmt, signed } from '../lib/format'
import { CaptionBadge, IconButton, StatusBadge } from '../shell/ui'
import { useExplorer } from '../state/store'
import type { Axis } from '../state/url'

interface Props {
  palette: Palette
  view: SceneView | undefined
  overlay: Overlay | undefined
  report: FeasibilityReport | undefined
  isLink: boolean
  scaleBar: { px: number; label: string }
}

function Toolbar({ isLink }: { isLink: boolean }) {
  const s = useExplorer()
  const sectionNext: Record<'off' | Axis, Axis | null> = { off: 'x', x: 'y', y: 'z', z: null }
  return (
    <div className="vp-toolbar" role="toolbar" aria-label="Viewport tools">
      <IconButton label="Fit all" shortcut="F" onClick={() => s.command({ kind: 'fit' })}>
        <Maximize size={16} />
      </IconButton>
      <IconButton
        label={s.projection === 'perspective' ? 'Orthographic view' : 'Perspective view'}
        shortcut="O"
        active={s.projection === 'orthographic'}
        onClick={() => s.setProjection(s.projection === 'perspective' ? 'orthographic' : 'perspective')}
      >
        <Box size={16} />
      </IconButton>
      <span className="vp-sep" />
      {!isLink && (
        <>
          <IconButton
            label={`Section view${s.sectionAxis ? ` (${s.sectionAxis.toUpperCase()})` : ''}`}
            shortcut="S"
            active={s.sectionAxis !== null}
            onClick={() => s.setSection(sectionNext[s.sectionAxis ?? 'off'])}
          >
            <Scissors size={16} />
            {s.sectionAxis && <span className="vp-axis">{s.sectionAxis.toUpperCase()}</span>}
          </IconButton>
          <IconButton
            label="Exploded view"
            shortcut="E"
            active={s.explode > 0}
            onClick={() => window.dispatchEvent(new CustomEvent('oicd:explode'))}
          >
            <Expand size={16} />
          </IconButton>
        </>
      )}
      <IconButton label="Measure" shortcut="M" active={s.measure} onClick={() => s.setMeasure(!s.measure)}>
        <Ruler size={16} />
      </IconButton>
      <span className="vp-sep" />
      <IconButton label="Labels" shortcut="L" active={s.labels} onClick={() => s.setFlag('labels', !s.labels)}>
        <Tags size={16} />
      </IconButton>
      {!isLink && (
        <>
          <IconButton label="Physics overlays" shortcut="V" active={s.overlays} onClick={() => s.setFlag('overlays', !s.overlays)}>
            <Lightbulb size={16} />
          </IconButton>
          <IconButton
            label="Tint SCHEMATIC parts"
            shortcut="T"
            active={s.tint}
            onClick={() => s.setFlag('tint', !s.tint)}
            data-testid="tint-toggle"
          >
            <SquareDashed size={16} />
          </IconButton>
        </>
      )}
      <IconButton label={s.still ? 'Play pulses' : 'Pause pulses'} shortcut="P" onClick={() => s.setFlag('still', !s.still)}>
        {s.still ? <Play size={16} /> : <Pause size={16} />}
      </IconButton>
    </div>
  )
}

function ScaleBar({ px, label }: { px: number; label: string }) {
  if (!Number.isFinite(px) || px <= 0) return null
  return (
    <div className="scale-bar" aria-label={`Scale bar: ${label}`}>
      <div className="scale-bar-line" style={{ width: `${Math.min(px, 400)}px` }} />
      <span data-testid="scale-label">{label}</span>
    </div>
  )
}

function ColorBar({ palette }: { palette: Palette }) {
  const lo = -palette.margin_range_db
  const span = 2 * palette.margin_range_db
  const bins = palette.margin_bins
  return (
    <div className="color-bar" aria-label="Margin color scale">
      <div className="color-bar-title">margin (dB)</div>
      <div className="color-bar-strip">
        {bins.map((b, i) => {
          const a = Math.max(b.lo_db ?? lo, lo)
          const z = Math.min(b.hi_db ?? -lo, -lo)
          const width = ((z - a) / span) * 100
          return width > 0 ? <span key={i} style={{ width: `${Math.max(width, 0.6)}%`, background: b.color }} /> : null
        })}
      </div>
      <div className="color-bar-ticks">
        {palette.margin_scale.map((t) => (
          <span key={t.value_db} style={{ left: `${((t.value_db - lo) / span) * 100}%` }}>
            {t.value_db > 0 ? `+${t.value_db}` : t.value_db < 0 ? `−${-t.value_db}` : '0'}
          </span>
        ))}
      </div>
    </div>
  )
}

function OverlayPanel({ overlay, palette }: { overlay: Overlay; palette: Palette }) {
  const overlayCase = useExplorer((s) => s.overlayCase)
  const setCase = useExplorer((s) => s.setOverlayCase)
  const isolation = useExplorer((s) => s.isolationDb)
  const setIsolation = useExplorer((s) => s.setIsolation)
  const [open, setOpen] = useState(false)
  const showsMargins = overlay.values.some((v) => v.margin_db !== null && v.margin_db !== undefined)
  const legend = [...new Map(overlay.paths.map((p) => [`${p.color}|${p.kind}|${p.label}`, p])).values()].slice(0, 6)
  const others = overlay.values.filter((v) => v.margin_db === null || v.margin_db === undefined)
  const bidi = overlay.scene === 'bidi_link' || overlay.scene === 'bidi_engine'
  return (
    <div className="overlay-panel" data-testid="overlay-panel">
      <div className="overlay-head">
        <div className="overlay-title">Physics overlay (API)</div>
        <button
          type="button"
          className="icon-btn"
          aria-expanded={open}
          aria-label={open ? 'Hide the legend and notes' : 'Show the legend and notes'}
          onClick={() => setOpen(!open)}
        >
          {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>
      {overlay.verdict && (
        <div className="overlay-verdict">
          <StatusBadge status={overlay.verdict} testId="overlay-verdict" />
          {overlay.margin_db !== null && (
            <span>
              power margin <span data-testid="overlay-margin">{signed(overlay.margin_db)}</span> dB
            </span>
          )}
        </div>
      )}
      {overlay.verdict_note && <p className="overlay-note">{overlay.verdict_note}</p>}
      {overlay.cases.length > 0 && (
        <ToggleGroup.Root
          type="single"
          value={overlay.case ?? overlayCase ?? ''}
          onValueChange={(v) => v && setCase(v)}
          aria-label="Reference-plane case"
          className="toggle-col"
          data-testid="case-toggle"
        >
          {overlay.cases.map((c) => (
            <ToggleGroup.Item key={c.id} value={c.id} className="toggle-item" data-testid={`case-${c.id}`}>
              {c.label}
            </ToggleGroup.Item>
          ))}
        </ToggleGroup.Root>
      )}
      {bidi && (
        <label className="overlay-slider">
          <span>diplexer isolation {fmt(isolation ?? 25, 1)} dB</span>
          <Slider.Root
            className="slider-root"
            min={0}
            max={60}
            step={0.5}
            value={[isolation ?? 25]}
            onValueChange={([v]) => v !== undefined && setIsolation(v)}
          >
            <Slider.Track className="slider-track">
              <Slider.Range className="slider-range" />
            </Slider.Track>
            <Slider.Thumb className="slider-thumb" aria-label="Diplexer isolation (dB)" />
          </Slider.Root>
        </label>
      )}
      {others.map((v) => (
        <p key={v.part} className="overlay-note">
          {v.label}
        </p>
      ))}
      {showsMargins && <ColorBar palette={palette} />}
      {open && (
        <>
          <ul className="overlay-legend">
            {legend.map((p, i) => (
              <li key={i}>
                <span className="legend-swatch" style={{ background: p.color, opacity: p.kind === 'ghost' ? 0.5 : 1 }} aria-hidden />
                <span>
                  {p.kind === 'ghost' ? 'ghost: ' : ''}
                  {p.label}
                </span>
              </li>
            ))}
          </ul>
          {overlay.legend && <p className="overlay-note">{overlay.legend}</p>}
          {overlay.notes.map((n) => (
            <p key={n} className="overlay-note">
              {n}
            </p>
          ))}
        </>
      )}
    </div>
  )
}

function TourBar({ view }: { view: SceneView }) {
  const stop = useExplorer((s) => s.tourStop)
  const setStop = useExplorer((s) => s.setTourStop)
  if (stop === null) return null
  const caption = view.captions[stop]
  if (caption === undefined) return null
  const total = view.captions.length
  return (
    <div className="tour-bar" role="dialog" aria-label="Guided tour">
      <div className="tour-head">
        <span className="tour-count">
          Stop {stop + 1} of {total}
        </span>
        <CaptionBadge badge={caption.badge} />
        <button type="button" className="icon-btn" aria-label="End tour" onClick={() => setStop(null)}>
          <X size={14} />
        </button>
      </div>
      <p className="tour-caption" data-testid="tour-caption">
        {caption.text}
      </p>
      <div className="tour-nav">
        <button type="button" className="btn" disabled={stop === 0} onClick={() => setStop(stop - 1)}>
          <ChevronLeft size={14} /> Previous
        </button>
        <button type="button" className="btn" disabled={stop + 1 >= total} onClick={() => setStop(stop + 1)}>
          Next <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

function Sliders({ isLink }: { isLink: boolean }) {
  const axis = useExplorer((s) => s.sectionAxis)
  const offset = useExplorer((s) => s.sectionOffset)
  const setOffset = useExplorer((s) => s.setSectionOffset)
  const explode = useExplorer((s) => s.explode)
  const setExplode = useExplorer((s) => s.setExplode)
  if (isLink) return null
  return (
    <div className="vp-sliders">
      <label className="vp-slider">
        <Layers size={14} aria-hidden />
        <span>explode</span>
        <Slider.Root
          className="slider-root"
          min={0}
          max={1}
          step={0.01}
          value={[explode]}
          onValueChange={([v]) => v !== undefined && setExplode(v)}
        >
          <Slider.Track className="slider-track">
            <Slider.Range className="slider-range" />
          </Slider.Track>
          <Slider.Thumb className="slider-thumb" aria-label="Explode" />
        </Slider.Root>
      </label>
      {axis !== null && (
        <label className="vp-slider">
          <Grid3x3 size={14} aria-hidden />
          <span>section {axis.toUpperCase()}</span>
          <Slider.Root
            className="slider-root"
            min={-0.5}
            max={0.5}
            step={0.005}
            value={[offset]}
            onValueChange={([v]) => v !== undefined && setOffset(v)}
          >
            <Slider.Track className="slider-track">
              <Slider.Range className="slider-range" />
            </Slider.Track>
            <Slider.Thumb className="slider-thumb" aria-label="Section position" />
          </Slider.Root>
        </label>
      )}
    </div>
  )
}

export function ViewportOverlays({ palette, view, overlay, report, isLink, scaleBar }: Props) {
  const clean = useExplorer((s) => s.clean)
  const overlays = useExplorer((s) => s.overlays)
  const measure = useExplorer((s) => s.measure)
  const info = view?.scene.scene
  return (
    <>
      {!clean && <Toolbar isLink={isLink} />}
      <div className="vp-caption">
        <div className="vp-title">{isLink ? (report?.link_name ?? 'Link') : (info?.name ?? 'Loading…')}</div>
        <div className="vp-sub">
          {isLink ? 'Schematic, not to scale' : `${info?.unit === 'um' ? 'µm' : info?.unit} · dimensions badged by class`}
        </div>
      </div>
      {isLink && report && (
        <div className={`badge ${report.verdict === 'EXCLUDED' ? 'badge-excluded' : 'badge-ok'}`} aria-live="polite">
          <div className="badge-verdict">{report.verdict}</div>
          <div className="badge-margin">margin {fmt(report.margin_db)} dB</div>
        </div>
      )}
      {measure && !clean && <div className="vp-hint">Measure: click two points (snaps to vertices and edges). Esc ends.</div>}
      {!isLink && <ScaleBar px={scaleBar.px} label={scaleBar.label} />}
      {!isLink && overlay && overlays && !clean && <OverlayPanel overlay={overlay} palette={palette} />}
      {!isLink && view && <TourBar view={view} />}
      {!clean && <Sliders isLink={isLink} />}
    </>
  )
}
