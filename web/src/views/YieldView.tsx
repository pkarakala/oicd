// Yield: the M_net histogram from POST /yield (model card §11), with the 0 dB line, the analytic
// and Monte Carlo yields, and per-element sigma sliders. Statistical, assumption-dependent; the
// worst-case verdict is shown unchanged next to it.

import { useProfile, useYield } from '../api/hooks'
import { fmt } from '../lib/format'
import { setSigma } from '../lib/linkEdits'
import { Empty, StatusBadge, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { NumberSlider } from './LinkBudget'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

export default function YieldView() {
  const palette = usePalette()
  const link = useExplorer((s) => s.design.link)
  const edit = useExplorer((s) => s.edit)
  const example = useProfile('yield_example')
  const hasSigma = link?.channel.some((e) => e.loss_distribution) ?? false
  const result = useYield(link, hasSigma)
  if (palette === undefined || link === null) return <Empty>Loading the design…</Empty>
  const data = result.data
  const h = data?.monte_carlo.histogram
  return (
    <div className="view view-yield" data-testid="yield-view">
      <div className="view-col view-side">
        {!hasSigma && (
          <button type="button" className="btn" disabled={example.data === undefined} onClick={() => example.data && edit((d) => ({ ...d, link: example.data }))} data-testid="load-yield">
            Load the model card §11 case (σ 0.2 dB per mating, SYNTHETIC)
          </button>
        )}
        {link.channel.map((e, i) => (
          <NumberSlider
            key={`${i}-${e.name}`}
            label={`σ ${e.name}`}
            unit="dB"
            value={e.loss_distribution?.sigma.value.value ?? 0}
            min={0}
            max={0.6}
            onChange={(v) => edit((d) => (d.link ? { ...d, link: setSigma(d.link, i, v) } : d))}
          />
        ))}
        {data && (
          <>
            <div className="verdict-row">
              <span className="muted small">worst case</span>
              <StatusBadge status={data.worst_case_verdict} />
              <span>{fmt(data.worst_case_margin_db)} dB</span>
            </div>
            <dl className="kv">
              <dt>yield (analytic)</dt>
              <dd data-testid="yield-analytic">{fmt(data.analytic.yield_fraction * 100, 3)} %</dd>
              <dt>yield (Monte Carlo)</dt>
              <dd>
                {fmt(data.monte_carlo.yield_fraction * 100, 3)} % ± {fmt(data.monte_carlo.standard_error * 100, 3)}
              </dd>
              <dt>σ total</dt>
              <dd>{fmt(data.analytic.sigma_total_db, 5)} dB</dd>
              <dt>margin at 3σ</dt>
              <dd>{fmt(data.analytic.margin_at_3sigma_db, 5)} dB</dd>
            </dl>
            <p className="muted small">{data.label}; seed {data.monte_carlo.seed}, {data.monte_carlo.n_samples} samples.</p>
          </>
        )}
      </div>
      <div className="view-col view-chart">
        {!hasSigma ? (
          <Empty>No loss distributions in this design: worst case only.</Empty>
        ) : h === undefined ? (
          <Empty>Sampling…</Empty>
        ) : (
          <Plot
            data={[
              {
                type: 'bar',
                x: h.edges_db.slice(0, -1).map((e, i) => (e + (h.edges_db[i + 1] ?? e)) / 2),
                y: h.counts,
                width: h.edges_db.slice(0, -1).map((e, i) => (h.edges_db[i + 1] ?? e) - e),
                marker: { color: palette.channels[0]?.color, line: { width: 0 } },
                hovertemplate: 'M_net %{x:.3f} dB: %{y} samples<extra></extra>',
              },
            ]}
            layout={baseLayout(palette, {
              margin: { l: 56, r: 16, t: 16, b: 44 },
              bargap: 0.04,
              xaxis: { title: { text: 'M_net (dB)' } },
              yaxis: { title: { text: 'samples' } },
              shapes: [{ type: 'line', x0: 0, x1: 0, yref: 'paper', y0: 0, y1: 1, line: { color: palette.ink, width: 1.5, dash: 'dash' } }],
              annotations: [{ x: 0, yref: 'paper', y: 1, text: '0 dB', showarrow: false, yanchor: 'bottom', font: { color: palette.ink } }],
            })}
            config={PLOT_CONFIG}
            useResizeHandler
            style={{ width: '100%', height: '100%' }}
          />
        )}
      </div>
    </div>
  )
}
