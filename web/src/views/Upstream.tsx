// Upstream: the laser splitting to N engines (model card §10), from POST /evaluate with the
// design's upstream chain; the engine reports P_TP2, the verdict and the maximum fan-out.

import type { FeasibilityReport } from '../api/client'
import { useProfile } from '../api/hooks'
import { fmt } from '../lib/format'
import { setSplit } from '../lib/linkEdits'
import { Empty, StatusBadge, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'

const MAX_N = 40

export default function Upstream({ report }: { report: FeasibilityReport | undefined }) {
  const palette = usePalette()
  const link = useExplorer((s) => s.design.link)
  const edit = useExplorer((s) => s.edit)
  const example = useProfile('upstream_example')
  if (palette === undefined || link === null) return <Empty>Loading the design…</Empty>
  const chain = link.tx.upstream
  if (chain === null || chain === undefined) {
    return (
      <div className="view">
        <Empty>
          This design has a fixed TP2 launch.{' '}
          <button
            type="button"
            className="btn"
            disabled={example.data === undefined}
            onClick={() => example.data && edit((d) => ({ ...d, link: example.data }))}
            data-testid="load-upstream"
          >
            Load the model card §10 laser chain (SYNTHETIC)
          </button>
        </Empty>
      </div>
    )
  }
  const upstream = report?.upstream
  const n = chain.split_n.value
  const fanout = upstream?.max_fanout
  const engines = Math.min(n, 24)
  return (
    <div className="view view-upstream" data-testid="upstream-view">
      <div className="view-col view-side">
        <label className="nslider">
          <span className="nslider-head">
            <span>fan-out N (1:N split)</span>
            <span className="nslider-value" data-testid="fanout-n">
              {n}
            </span>
          </span>
          <input
            type="range"
            min={1}
            max={MAX_N}
            step={1}
            value={n}
            aria-label="fan-out N"
            onChange={(e) => edit((d) => (d.link ? { ...d, link: setSplit(d.link, Number(e.target.value)) } : d))}
          />
          {fanout !== undefined && (
            <span className="fanout-marker" style={{ left: `${((fanout - 1) / (MAX_N - 1)) * 100}%` }} title={`max fan-out ${fanout}`}>
              ▲ max {fanout}
            </span>
          )}
        </label>
        {report && (
          <div className="verdict-row">
            <StatusBadge status={report.verdict} testId="upstream-verdict" />
            <span>
              margin <span data-testid="upstream-margin">{fmt(report.margin_db)}</span> dB
            </span>
          </div>
        )}
        {upstream && (
          <dl className="kv">
            <dt>P_TP2 average</dt>
            <dd>{fmt(upstream.p_tp2_avg_dbm)} dBm</dd>
            <dt>P_TP2 OMA</dt>
            <dd>{fmt(upstream.p_tp2_oma_dbm)} dBm</dd>
            <dt>maximum fan-out</dt>
            <dd data-testid="max-fanout">{upstream.max_fanout}</dd>
          </dl>
        )}
        <p className="muted small">{upstream?.derivation}</p>
      </div>
      <div className="view-col view-chart">
        <svg viewBox="0 0 420 220" className="fanout-svg" role="img" aria-label={`Laser split to ${n} engines`}>
          <rect x={10} y={90} width={60} height={40} rx={4} fill={palette.muted} />
          <text x={40} y={145} fontSize={10} textAnchor="middle" fill={palette.ink}>
            laser
          </text>
          {Array.from({ length: engines }, (_, i) => {
            const y = 12 + (i * 196) / Math.max(engines - 1, 1)
            const beyond = fanout !== undefined && i + 1 > fanout
            return (
              <g key={i}>
                <path d={`M70 110 C 180 110, 220 ${y}, 330 ${y}`} fill="none" stroke={palette.cw} strokeWidth={1.2} opacity={beyond ? 0.35 : 0.9} />
                <rect x={332} y={y - 4} width={22} height={8} rx={2} fill={beyond ? palette.grid : palette.ink} />
              </g>
            )
          })}
          {n > engines && (
            <text x={360} y={214} fontSize={10} fill={palette.muted}>
              + {n - engines} more
            </text>
          )}
          <text x={360} y={12} fontSize={10} fill={palette.ink}>
            N = {n}
          </text>
        </svg>
        {upstream && (
          <table className="steps">
            <tbody>
              {upstream.steps.map((s) => (
                <tr key={s.input_path}>
                  <td>{s.name}</td>
                  <td className="mono">{s.loss_db === null ? '' : `−${fmt(s.loss_db)} dB`}</td>
                  <td className="mono">
                    {fmt(s.power_dbm)} dBm {s.kind}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
