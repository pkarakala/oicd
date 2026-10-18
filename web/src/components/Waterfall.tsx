import Plotly from 'plotly.js-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'
import { displayName, fmt } from '../format'
import type { FeasibilityReport } from '../types'

const Plot = createPlotlyComponent(Plotly)

interface Props {
  report: FeasibilityReport
  hovered: number | null
  onHover: (index: number | null) => void
}

interface HoverEvent {
  points?: { customdata?: unknown }[]
}

/** OMA at each plane of power_trace. Loss elements are floating bars drawn from the power after
 * the element (base) up by the element's loss_db, both values straight from the API; Plotly only
 * renders them. Reference planes are markers at their OMA. */
export function Waterfall({ report, hovered, onHover }: Props) {
  const trace = report.power_trace
  const indices = trace.map((_, i) => i)
  const losses = indices.filter((i) => trace[i]?.kind === 'loss_element')
  const planes = indices.filter((i) => trace[i]?.kind === 'reference_plane')
  const tp3Index = trace.length - 1
  const tp3 = trace[tp3Index]
  const excluded = report.verdict === 'EXCLUDED'

  const data = [
    {
      type: 'bar',
      name: 'loss element',
      x: losses,
      base: losses.map((i) => trace[i]?.power_dbm),
      y: losses.map((i) => trace[i]?.loss_db),
      customdata: losses,
      text: losses.map((i) => `−${fmt(trace[i]?.loss_db ?? 0)} dB`),
      textposition: 'outside',
      hovertext: losses.map(
        (i) => `${trace[i]?.name}<br>loss ${fmt(trace[i]?.loss_db ?? 0)} dB<br>OMA after ${fmt(trace[i]?.power_dbm ?? 0)} dBm`,
      ),
      hoverinfo: 'text',
      marker: {
        // Hue from the API's above_threshold flag only (review R1).
        color: losses.map((i) => (trace[i]?.above_threshold ? '#22c55e' : '#ef4444')),
        opacity: losses.map((i) => (hovered === null || hovered === i ? 0.95 : 0.45)),
        line: { color: '#fbbf24', width: losses.map((i) => (hovered === i ? 3 : 0)) },
      },
    },
    {
      type: 'scatter',
      mode: 'markers+text',
      name: 'reference plane',
      x: planes,
      y: planes.map((i) => trace[i]?.power_dbm),
      customdata: planes,
      text: planes.map((i) => `${fmt(trace[i]?.power_dbm ?? 0)} dBm`),
      textposition: 'top center',
      hovertext: planes.map((i) => `${trace[i]?.name}<br>OMA ${fmt(trace[i]?.power_dbm ?? 0)} dBm`),
      hoverinfo: 'text',
      marker: {
        symbol: 'diamond',
        size: planes.map((i) => (hovered === i ? 18 : 13)),
        color: '#60a5fa',
        line: { color: '#fbbf24', width: planes.map((i) => (hovered === i ? 3 : 0)) },
      },
    },
  ]

  const layout = {
    autosize: true,
    margin: { l: 56, r: 24, t: 28, b: 64 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#cbd5e1', size: 11 },
    showlegend: false,
    hovermode: 'closest',
    bargap: 0.45,
    xaxis: {
      tickvals: indices,
      ticktext: trace.map((p) => (p.kind === 'reference_plane' ? displayName(report, p) : p.name)),
      gridcolor: '#1e293b',
    },
    yaxis: { title: { text: 'OMA (dBm)' }, gridcolor: '#1e293b', zeroline: false },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        y0: report.threshold_dbm,
        y1: report.threshold_dbm,
        line: { color: '#f87171', width: 2, dash: 'dash' },
      },
    ],
    annotations: [
      {
        xref: 'paper',
        x: 0,
        xanchor: 'left',
        y: report.threshold_dbm,
        yanchor: 'top',
        text: `threshold ${fmt(report.threshold_dbm)} dBm`,
        showarrow: false,
        font: { color: '#f87171' },
      },
      ...(tp3 === undefined
        ? []
        : [
            {
              x: tp3Index,
              y: tp3.power_dbm,
              text: `margin ${fmt(report.margin_db)} dB`,
              showarrow: true,
              arrowcolor: excluded ? '#ef4444' : '#22c55e',
              ax: excluded ? -110 : -70,
              ay: excluded ? -60 : 36,
              font: { color: excluded ? '#fca5a5' : '#86efac', size: 13 },
              bgcolor: '#0f172a',
              bordercolor: excluded ? '#ef4444' : '#22c55e',
            },
          ]),
    ],
  }

  const pick = (event: HoverEvent) => {
    const index = event.points?.[0]?.customdata
    onHover(typeof index === 'number' ? index : null)
  }

  return (
    <Plot
      data={data}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      onHover={pick}
      onUnhover={() => onHover(null)}
    />
  )
}
