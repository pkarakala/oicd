// Plotly, loaded with the chart views (code-split). Layout colors come from the API palette.

import Plotly from 'plotly.js-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'
import type { Palette } from '../api/client'

export const Plot = createPlotlyComponent(Plotly)

export function baseLayout(palette: Palette, extra: Record<string, unknown> = {}): Record<string, unknown> {
  const axis = { gridcolor: palette.grid, zerolinecolor: palette.grid, linecolor: palette.grid, tickcolor: palette.muted }
  return {
    autosize: true,
    margin: { l: 58, r: 20, t: 26, b: 48 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: palette.ink, size: 11, family: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif' },
    hoverlabel: { bgcolor: palette.surface, bordercolor: palette.grid, font: { color: palette.ink } },
    showlegend: false,
    ...extra,
    xaxis: { ...axis, ...((extra.xaxis as object | undefined) ?? {}) },
    yaxis: { ...axis, ...((extra.yaxis as object | undefined) ?? {}) },
  }
}

export const PLOT_CONFIG = { displayModeBar: false, responsive: true }
