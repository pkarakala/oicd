// Design space: margin over two inputs from POST /sweep (model card §8), with the engine's 0 dB
// contour, the current design marked; clicking a cell loads that design (an undoable edit).

import { useMemo } from 'react'
import type { Link } from '../api/client'
import { useSweep } from '../api/hooks'
import { fmt } from '../lib/format'
import { pathValue, setPath } from '../lib/linkEdits'
import { Empty, StatusBadge, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

const POINTS = 41

function axes(link: Link) {
  const patch = Math.max(0, link.channel.findIndex((e) => /patch/i.test(e.name)))
  const xPath = `channel[${patch}].loss_max`
  const yPath = link.tx.launch_oma_min ? 'tx.launch_oma_min' : 'rx.sensitivity_oma_max'
  const xv = pathValue(link, xPath) ?? 1
  const yv = pathValue(link, yPath) ?? 0
  return {
    x: { path: xPath, start: Math.max(0, xv - 2), stop: Math.max(0, xv - 2) + 4, num: POINTS },
    y: { path: yPath, start: yv - 2, stop: yv + 2, num: POINTS },
    xLabel: `${link.channel[patch]?.name ?? 'element'} loss (dB)`,
    yLabel: yPath === 'tx.launch_oma_min' ? 'TX launch OMA (dBm)' : 'RX sensitivity OMA (dBm)',
  }
}

interface ClickEvent {
  points?: { x?: unknown; y?: unknown }[]
}

export default function DesignSpace() {
  const palette = usePalette()
  const link = useExplorer((s) => s.design.link)
  const edit = useExplorer((s) => s.edit)
  // the axes stay put while designs load from the grid; they change only with the link's shape
  const shape = link ? `${link.name}|${link.tx.launch_oma_min ? 'fixed' : 'chain'}|${link.channel.length}` : ''
  const ax = useMemo(() => (link ? axes(link) : null), [shape])
  const sweep = useSweep(link, ax?.x ?? { path: '', start: 0, stop: 0, num: 1 }, ax?.y ?? { path: '', start: 0, stop: 0, num: 1 }, ax !== null)
  if (palette === undefined || link === null || ax === null) return <Empty>Loading the design…</Empty>
  const result = sweep.data
  if (result === undefined) return <Empty>{sweep.isError ? String(sweep.error) : 'Sweeping…'}</Empty>
  const lo = -palette.margin_range_db
  const span = 2 * palette.margin_range_db
  // stepped colorscale from the API's margin bins
  const colorscale: [number, string][] = []
  for (const b of palette.margin_bins) {
    const a = Math.min(Math.max(((b.lo_db ?? lo) - lo) / span, 0), 1)
    const z = Math.min(Math.max(((b.hi_db ?? -lo) - lo) / span, 0), 1)
    if (z <= a) continue
    colorscale.push([a, b.color], [z, b.color])
  }
  const cx: (number | null)[] = []
  const cy: (number | null)[] = []
  for (const [[x0, y0], [x1, y1]] of result.contour_0db) {
    cx.push(x0, x1, null)
    cy.push(y0, y1, null)
  }
  const data = [
    {
      type: 'heatmap',
      x: result.x.values,
      y: result.y.values,
      z: result.margin_db,
      zmin: lo,
      zmax: -lo,
      colorscale,
      colorbar: { title: { text: 'margin (dB)' }, thickness: 10, len: 0.9, outlinewidth: 0 },
      hovertemplate: `${ax.xLabel} %{x:.3f}<br>${ax.yLabel} %{y:.3f}<br>margin %{z:.4f} dB<extra></extra>`,
    },
    {
      type: 'scatter',
      mode: 'lines',
      x: cx,
      y: cy,
      line: { color: palette.ink, width: 2 },
      hoverinfo: 'skip',
      connectgaps: false,
    },
    {
      type: 'scatter',
      mode: 'markers+text',
      x: [result.design.x],
      y: [result.design.y],
      text: [`design ${fmt(result.design.margin_db)} dB`],
      textposition: 'top center',
      marker: { symbol: 'x-thin', size: 14, line: { width: 3, color: palette.ink } },
      hoverinfo: 'skip',
    },
  ]
  const layout = baseLayout(palette, {
    margin: { l: 60, r: 10, t: 16, b: 46 },
    xaxis: { title: { text: ax.xLabel } },
    yaxis: { title: { text: ax.yLabel } },
  })
  const onClick = (event: ClickEvent) => {
    const p = event.points?.[0]
    if (typeof p?.x !== 'number' || typeof p.y !== 'number') return
    const [x, y] = [p.x, p.y]
    edit((d) => (d.link ? { ...d, link: setPath(setPath(d.link, ax.x.path, x), ax.y.path, y) } : d))
  }
  return (
    <div className="view view-design" data-testid="design-space">
      <div className="view-col view-side">
        <div className="verdict-row">
          <StatusBadge status={result.design.verdict} />
          <span>design margin {fmt(result.design.margin_db)} dB</span>
        </div>
        <dl className="kv">
          <dt>x</dt>
          <dd>
            <code>{result.x.path}</code> ({result.x.unit})
          </dd>
          <dt>y</dt>
          <dd>
            <code>{result.y.path}</code> ({result.y.unit})
          </dd>
          <dt>best cell</dt>
          <dd>
            {fmt(result.best.margin_db)} dB at ({fmt(result.best.x, 3)}, {fmt(result.best.y, 3)})
          </dd>
          <dt>worst cell</dt>
          <dd>
            {fmt(result.worst.margin_db)} dB at ({fmt(result.worst.x, 3)}, {fmt(result.worst.y, 3)})
          </dd>
        </dl>
        <p className="muted small">Black line: the engine's 0 dB contour. Click a cell to load that design (undo with ⌘Z).</p>
      </div>
      <div className="view-col view-chart">
        <Plot data={data} layout={layout} config={PLOT_CONFIG} useResizeHandler style={{ width: '100%', height: '100%' }} onClick={onClick} />
      </div>
    </div>
  )
}
