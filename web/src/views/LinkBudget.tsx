// Link budget (the brief 03 view): inputs that POST the whole Link, the OMA waterfall and the
// checks. Every number is the engine's; edits are SYNTHETIC what-ifs with undo and redo.

import { useEffect, useState } from 'react'
import type { CheckResult, FeasibilityReport, Link } from '../api/client'
import { LINK_SCENE } from '../api/hooks'
import { displayName, fmt } from '../lib/format'
import { addConnector, setLaunch, setLoss, setPenalty, setReserve, setSensitivity } from '../lib/linkEdits'
import { enterScene } from '../shell/navigation'
import { Empty, StatusBadge, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

interface SliderProps {
  label: string
  unit: string
  value: number
  min: number
  max: number
  onChange: (value: number) => void
}

/** Slider plus a number box. The slider range is a UI convenience; the number box accepts any
 * value and the engine decides whether it is valid physics. */
export function NumberSlider({ label, unit, value, min, max, onChange }: SliderProps) {
  const [text, setText] = useState(String(value))
  useEffect(() => setText(String(value)), [value])
  const commit = (raw: string) => {
    setText(raw)
    const parsed = Number(raw)
    if (raw.trim() !== '' && Number.isFinite(parsed)) onChange(parsed)
  }
  return (
    <div className="nslider">
      <div className="nslider-head">
        <span>{label}</span>
        <span className="nslider-value">
          <input type="number" step="any" aria-label={`${label} (${unit})`} value={text} onChange={(e) => commit(e.target.value)} />
          {unit}
        </span>
      </div>
      <input
        type="range"
        step="any"
        min={min}
        max={max}
        aria-label={`${label} slider`}
        value={Math.min(Math.max(value, min), max)}
        onChange={(e) => commit(e.target.value)}
      />
    </div>
  )
}

function Controls({ link }: { link: Link }) {
  const edit = useExplorer((s) => s.edit)
  const change = (next: (l: Link) => Link) => edit((d) => (d.link ? { ...d, link: next(d.link) } : d))
  const launch = link.tx.launch_oma_min
  return (
    <section className="controls" aria-label="Controls">
      <h3>Transmitter and receiver</h3>
      {launch ? (
        <NumberSlider label="TX launch OMA" unit="dBm" value={launch.value.power_dbm.value} min={-10} max={6} onChange={(v) => change((l) => setLaunch(l, v))} />
      ) : (
        <p className="muted small">TP2 is derived from the upstream laser chain (see the Upstream tab).</p>
      )}
      <NumberSlider
        label="RX sensitivity OMA"
        unit="dBm"
        value={link.rx.sensitivity_oma_max.value.power_dbm.value}
        min={-14}
        max={0}
        onChange={(v) => change((l) => setSensitivity(l, v))}
      />
      <h3>Channel (TP2 to TP3)</h3>
      {link.channel.map((element, i) => (
        <NumberSlider
          key={`${i}-${element.name}`}
          label={`${element.name} loss`}
          unit="dB"
          value={element.loss_max.value.value}
          min={0}
          max={6}
          onChange={(v) => change((l) => setLoss(l, i, v))}
        />
      ))}
      <button type="button" className="btn" onClick={() => change(addConnector)}>
        Add connector
      </button>
      <h3>Penalties and reserve</h3>
      {link.penalties.length === 0 && <p className="muted small">No named penalties in this link.</p>}
      {link.penalties.map((penalty, i) => (
        <NumberSlider
          key={`${i}-${penalty.name}`}
          label={`${penalty.name} penalty`}
          unit="dB"
          value={penalty.value.value.value}
          min={0}
          max={5}
          onChange={(v) => change((l) => setPenalty(l, i, v))}
        />
      ))}
      <NumberSlider label="Reserve" unit="dB" value={link.reserve.value.value} min={0} max={5} onChange={(v) => change((l) => setReserve(l, v))} />
    </section>
  )
}

interface HoverEvent {
  points?: { customdata?: unknown }[]
}

/** OMA at each plane of power_trace: loss elements as floating bars from the power after the
 * element up by its loss, reference planes as markers; bar hue from the API's above_threshold. */
export function Waterfall({ report }: { report: FeasibilityReport }) {
  const palette = usePalette()
  const hovered = useExplorer((s) => s.hovered)
  const hover = useExplorer((s) => s.hover)
  if (palette === undefined) return null
  const trace = report.power_trace
  const indices = trace.map((_, i) => i)
  const losses = indices.filter((i) => trace[i]?.kind === 'loss_element')
  const planes = indices.filter((i) => trace[i]?.kind === 'reference_plane')
  const good = palette.status.find((s) => s.key === 'NOT_EXCLUDED')?.color
  const bad = palette.status.find((s) => s.key === 'EXCLUDED')?.color
  const tp3Index = trace.length - 1
  const tp3 = trace[tp3Index]
  const excluded = report.verdict === 'EXCLUDED'
  const isHovered = (i: number) => trace[i]?.name === hovered
  const data = [
    {
      type: 'bar',
      x: losses,
      base: losses.map((i) => trace[i]?.power_dbm),
      y: losses.map((i) => trace[i]?.loss_db),
      customdata: losses,
      text: losses.map((i) => `−${fmt(trace[i]?.loss_db ?? 0)} dB`),
      textposition: 'outside',
      hovertext: losses.map((i) => `${trace[i]?.name}<br>loss ${fmt(trace[i]?.loss_db ?? 0)} dB<br>OMA after ${fmt(trace[i]?.power_dbm ?? 0)} dBm`),
      hoverinfo: 'text',
      marker: {
        color: losses.map((i) => (trace[i]?.above_threshold ? good : bad)),
        opacity: losses.map((i) => (hovered === null || isHovered(i) ? 0.95 : 0.5)),
        line: { color: palette.ink, width: losses.map((i) => (isHovered(i) ? 2 : 0)) },
      },
    },
    {
      type: 'scatter',
      mode: 'markers+text',
      x: planes,
      y: planes.map((i) => trace[i]?.power_dbm),
      customdata: planes,
      text: planes.map((i) => `${fmt(trace[i]?.power_dbm ?? 0)} dBm`),
      textposition: 'top center',
      hovertext: planes.map((i) => `${trace[i]?.name}<br>OMA ${fmt(trace[i]?.power_dbm ?? 0)} dBm`),
      hoverinfo: 'text',
      marker: { symbol: 'diamond', size: planes.map((i) => (isHovered(i) ? 16 : 12)), color: palette.ink },
    },
  ]
  const layout = baseLayout(palette, {
    margin: { l: 56, r: 16, t: 20, b: 70 },
    bargap: 0.45,
    hovermode: 'closest',
    xaxis: { tickvals: indices, ticktext: trace.map((p) => (p.kind === 'reference_plane' ? displayName(report, p) : p.name)) },
    yaxis: { title: { text: 'OMA (dBm)' }, zeroline: false },
    shapes: [
      { type: 'line', xref: 'paper', x0: 0, x1: 1, y0: report.threshold_dbm, y1: report.threshold_dbm, line: { color: palette.muted, width: 1.5, dash: 'dash' } },
    ],
    annotations: [
      { xref: 'paper', x: 0, xanchor: 'left', y: report.threshold_dbm, yanchor: 'top', text: `threshold ${fmt(report.threshold_dbm)} dBm`, showarrow: false, font: { color: palette.muted } },
      ...(tp3 === undefined
        ? []
        : [
            {
              x: tp3Index,
              y: tp3.power_dbm,
              text: `margin ${fmt(report.margin_db)} dB`,
              showarrow: true,
              arrowcolor: excluded ? bad : good,
              ax: -80,
              ay: excluded ? -40 : 30,
              font: { color: palette.ink, size: 12 },
              bgcolor: palette.surface,
              bordercolor: excluded ? bad : good,
            },
          ]),
    ],
  })
  const pick = (event: HoverEvent) => {
    const index = event.points?.[0]?.customdata
    hover(typeof index === 'number' ? (trace[index]?.name ?? null) : null)
  }
  return (
    <Plot
      data={data}
      layout={layout}
      config={PLOT_CONFIG}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      onHover={pick}
      onUnhover={() => hover(null)}
    />
  )
}

function Result({ result }: { result: CheckResult }) {
  return (
    <li className={`result result-${result.status}`}>
      <div>
        <span className="status">{result.status.toUpperCase()}</span> <code>{result.constraint}</code>
      </div>
      <div className="muted small">{result.message}</div>
    </li>
  )
}

export function ChecksPanel({ report }: { report: FeasibilityReport }) {
  return (
    <details className="checks" open>
      <summary>
        Checks ({report.results.length} evaluated, {report.not_evaluated.length} not evaluated)
      </summary>
      <ul>
        {report.results.map((r) => (
          <Result key={r.constraint} result={r} />
        ))}
      </ul>
      <h3>Not evaluated</h3>
      <ul>
        {report.not_evaluated.map((r) => (
          <Result key={r.constraint} result={r} />
        ))}
      </ul>
    </details>
  )
}

export default function LinkBudget({ report, pending }: { report: FeasibilityReport | undefined; pending: boolean }) {
  const link = useExplorer((s) => s.design.link)
  const scene = useExplorer((s) => s.scene)
  if (link === null || report === undefined) return <Empty>Evaluating the worked example…</Empty>
  return (
    <div className="view view-budget">
      <div className="view-col view-controls">
        <div className="verdict-row">
          <StatusBadge status={report.verdict} />
          <span data-testid="verdict" className="verdict-text">
            {report.verdict}
          </span>
          <span>
            margin <span data-testid="margin">{fmt(report.margin_db)}</span> dB
          </span>
          {pending && <span className="muted small"> · updating</span>}
        </div>
        <p className="muted small">{report.link_name}</p>
        {scene !== LINK_SCENE && (
          <button type="button" className="btn" onClick={() => enterScene(LINK_SCENE)}>
            Show this link in 3D
          </button>
        )}
        <Controls link={link} />
      </div>
      <div className="view-col view-chart">
        <Waterfall report={report} />
      </div>
      <div className="view-col view-checks">
        <ChecksPanel report={report} />
      </div>
    </div>
  )
}
