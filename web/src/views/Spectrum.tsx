// Spectrum: the interleaved 16λ grid with ±accuracy bars and every receive ring's drop response,
// all from GET /spectrum/bidi16 (catalog inputs); the ring-FSR hypothesis is the only choice here.

import * as ToggleGroup from '@radix-ui/react-toggle-group'
import { useSpectrum } from '../api/hooks'
import { num } from '../lib/format'
import { CaptionBadge, Empty, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { SPECTRUM_HYPOTHESES, type SpectrumHypothesis } from '../state/url'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

export default function Spectrum() {
  const palette = usePalette()
  const hypothesis = useExplorer((s) => s.spectrumHypothesis)
  const setHypothesis = useExplorer((s) => s.setSpectrumHypothesis)
  const spectrum = useSpectrum(hypothesis, true)
  const data = spectrum.data
  if (palette === undefined) return null
  if (data === undefined) return <Empty>Computing ring responses…</Empty>
  const x = data.crosstalk
  const color = (n: number) => palette.channels[n]?.color ?? palette.muted
  const traces = x.spectra.map((s) => ({
    type: 'scatter',
    mode: 'lines',
    x: x.frequency_ghz,
    y: s.drop_db,
    line: { color: color(s.channel), width: s.channel === x.worst.channel ? 2.4 : 1.2 },
    hovertemplate: `ring on channel ${s.channel}<br>%{x:.0f} GHz: %{y:.2f} dB<extra></extra>`,
  }))
  const shapes = x.grid.channels.flatMap((c) => [
    {
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: c.frequency_ghz - data.accuracy_ghz,
      x1: c.frequency_ghz + data.accuracy_ghz,
      y0: 0,
      y1: 1,
      fillcolor: color(c.index),
      opacity: 0.16,
      line: { width: 0 },
    },
    {
      type: 'line',
      xref: 'x',
      yref: 'paper',
      x0: c.frequency_ghz,
      x1: c.frequency_ghz,
      y0: 0,
      y1: 1,
      line: { color: color(c.index), width: 1, dash: x.receive_channels.includes(c.index) ? 'solid' : 'dot' },
    },
  ])
  const worst = x.worst
  const worstChannel = x.grid.channels[worst.channel]
  const layout = baseLayout(palette, {
    margin: { l: 56, r: 16, t: 22, b: 44 },
    xaxis: { title: { text: 'frequency (GHz)' }, tickformat: ',.0f' },
    yaxis: { title: { text: 'drop response (dB)' }, range: [-45, 2] },
    shapes,
    annotations: worstChannel
      ? [
          {
            x: worstChannel.frequency_ghz,
            y: 0,
            yanchor: 'bottom',
            text: `worst receive channel ${worst.channel}: X ${num(worst.leakage, 5)}, ${num(worst.crosstalk_db, 4)} dB`,
            showarrow: true,
            ay: 34,
            font: { color: palette.ink },
            bgcolor: palette.surface,
          },
        ]
      : [],
  })
  return (
    <div className="view view-spectrum">
      <div className="view-col view-side">
        <ToggleGroup.Root
          type="single"
          value={hypothesis}
          onValueChange={(v) => v && setHypothesis(v as SpectrumHypothesis)}
          className="toggle-col"
          aria-label="Ring FSR hypothesis"
        >
          {SPECTRUM_HYPOTHESES.map((h) => (
            <ToggleGroup.Item key={h} value={h} className="toggle-item">
              {h}
            </ToggleGroup.Item>
          ))}
        </ToggleGroup.Root>
        <p className="small">{data.statement}</p>
        <dl className="kv">
          <dt>ring FSR</dt>
          <dd>{num(data.fsr_ghz)} GHz</dd>
          <dt>loaded Q</dt>
          <dd>{num(data.q_loaded)}</dd>
          <dt>FWHM</dt>
          <dd>{num(x.fwhm_ghz, 6)} GHz</dd>
          <dt>grid accuracy</dt>
          <dd>±{num(data.accuracy_ghz)} GHz (bars)</dd>
          <dt>worst channel</dt>
          <dd data-testid="spectrum-worst">
            {worst.channel}: crosstalk {num(worst.crosstalk_db, 4)} dB
          </dd>
        </dl>
        <p className="muted small">
          {palette.channel_legend} Solid lines: receive channels (direction B, odd n); dotted: local transmit channels.
        </p>
        <div className="row-badges">
          <CaptionBadge badge="inference" />
        </div>
        <p className="muted small">Inputs: {data.inputs.join(', ')}</p>
      </div>
      <div className="view-col view-chart">
        <Plot data={traces} layout={layout} config={PLOT_CONFIG} useResizeHandler style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  )
}
