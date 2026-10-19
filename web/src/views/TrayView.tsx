// Tray: N copies of the design link with per-lane edits, from POST /evaluate_tray (model card §9):
// lanes as parallel fibers colored by margin, the engine's deciding lane highlighted, margin bars.

import { useMemo, useState } from 'react'
import type { Link } from '../api/client'
import { useTray } from '../api/hooks'
import { fmt, marginColor } from '../lib/format'
import { setLoss } from '../lib/linkEdits'
import { Empty, StatusBadge, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { NumberSlider } from './LinkBudget'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

export default function TrayView() {
  const palette = usePalette()
  const design = useExplorer((s) => s.design)
  const edit = useExplorer((s) => s.edit)
  const [lane, setLane] = useState(0)
  const link = design.link
  const patch = link ? Math.max(0, link.channel.findIndex((e) => /patch/i.test(e.name))) : 0
  const lanes = useMemo(() => {
    if (link === null) return null
    return Array.from({ length: design.lanes }, (_, i): Link => {
      const loss = design.laneEdits[i]
      const named = { ...link, name: `lane ${i + 1}` }
      return loss === undefined ? named : setLoss(named, patch, loss)
    })
  }, [link, design.lanes, design.laneEdits, patch])
  const tray = useTray(lanes, lanes !== null)
  if (palette === undefined || link === null) return <Empty>Loading the design…</Empty>
  const report = tray.data
  const selected = Math.min(lane, design.lanes - 1)
  const laneLoss = design.laneEdits[selected] ?? link.channel[patch]?.loss_max.value.value ?? 0
  return (
    <div className="view view-tray" data-testid="tray-view">
      <div className="view-col view-side">
        <NumberSlider
          label="lanes"
          unit=""
          value={design.lanes}
          min={1}
          max={16}
          onChange={(v) => edit((d) => ({ ...d, lanes: Math.min(Math.max(Math.round(v), 1), 64) }))}
        />
        <div className="lane-picker" role="group" aria-label="Lane">
          {Array.from({ length: design.lanes }, (_, i) => (
            <button key={i} type="button" className={`lane-btn ${i === selected ? 'is-active' : ''}`} onClick={() => setLane(i)} aria-pressed={i === selected}>
              {i + 1}
            </button>
          ))}
        </div>
        <NumberSlider
          label={`lane ${selected + 1} ${link.channel[patch]?.name ?? 'element'} loss`}
          unit="dB"
          value={laneLoss}
          min={0}
          max={6}
          onChange={(v) => edit((d) => ({ ...d, laneEdits: { ...d.laneEdits, [selected]: v } }))}
        />
        <button type="button" className="btn" onClick={() => edit((d) => ({ ...d, laneEdits: {} }))}>
          Reset lanes
        </button>
        {report && (
          <div className="verdict-row">
            <StatusBadge status={report.verdict} testId="tray-verdict" />
            <span>
              tray margin <span data-testid="tray-margin">{fmt(report.margin_db)}</span> dB, deciding lane{' '}
              <span data-testid="tray-deciding">{report.deciding_lane + 1}</span>
            </span>
          </div>
        )}
      </div>
      <div className="view-col view-chart tray-chart">
        {report === undefined ? (
          <Empty>Evaluating the tray…</Empty>
        ) : (
          <>
            <svg className="tray-fibers" viewBox={`0 0 220 ${report.lanes.length * 22 + 10}`} role="img" aria-label="Lanes as parallel fibers">
              {report.lanes.map((l) => {
                const deciding = l.index === report.deciding_lane
                const y = 14 + l.index * 22
                return (
                  <g key={l.index}>
                    <text x={4} y={y + 4} fontSize={10} fill={palette.ink}>
                      {l.index + 1}
                    </text>
                    <line x1={24} x2={214} y1={y} y2={y} stroke={marginColor(palette.margin_bins, l.margin_db)} strokeWidth={deciding ? 7 : 4} strokeLinecap="round" />
                    {deciding && (
                      <text x={214} y={y - 6} fontSize={9} textAnchor="end" fill={palette.ink}>
                        deciding lane
                      </text>
                    )}
                  </g>
                )
              })}
            </svg>
            <Plot
              data={[
                {
                  type: 'bar',
                  orientation: 'h',
                  y: report.lanes.map((l) => `lane ${l.index + 1}`),
                  x: report.lanes.map((l) => l.margin_db),
                  marker: {
                    color: report.lanes.map((l) => marginColor(palette.margin_bins, l.margin_db)),
                    line: { color: palette.ink, width: report.lanes.map((l) => (l.index === report.deciding_lane ? 2 : 0)) },
                  },
                  text: report.lanes.map((l) => `${fmt(l.margin_db)} dB ${l.verdict === 'EXCLUDED' ? '✕' : ''}`),
                  textposition: 'auto',
                  insidetextanchor: 'middle',
                  hovertemplate: '%{y}: %{x:.4f} dB<extra></extra>',
                },
              ]}
              layout={baseLayout(palette, {
                margin: { l: 56, r: 40, t: 10, b: 36 },
                yaxis: { autorange: 'reversed' },
                xaxis: { title: { text: 'lane margin (dB)' }, zeroline: true, zerolinecolor: palette.ink },
              })}
              config={PLOT_CONFIG}
              useResizeHandler
              style={{ width: '100%', height: '100%' }}
            />
          </>
        )}
      </div>
    </div>
  )
}
