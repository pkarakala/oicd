// Inference: the product's evaluated graph from the API, laid out with elkjs and colored by class;
// click a node for its derivation chain. Hypothesis toggles re-evaluate through POST /inference;
// the support matrix, tornado and conflicts are the engine's.

import type { ElkExtendedEdge, ElkNode } from 'elkjs/lib/elk-api'
import ELK from 'elkjs/lib/elk.bundled.js'
import { Minus, Plus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { BibEntry, EvaluatedGraph, NodeResult, ProductView } from '../api/client'
import { useReferences } from '../api/hooks'
import { num } from '../lib/format'
import { NodeCard } from '../shell/Inspector'
import { ClassBadge, Empty, Section, StatusBadge, Tip, usePalette } from '../shell/ui'
import { useExplorer } from '../state/store'
import { PLOT_CONFIG, Plot, baseLayout } from './Plot'

const NODE_W = 196
const NODE_H = 38

interface Laid {
  nodes: { id: string; x: number; y: number; kind: 'node' | 'check' }[]
  edges: { id: string; points: [number, number][] }[]
  width: number
  height: number
}

const elk = new ELK()

function useLayout(graph: EvaluatedGraph | undefined): Laid | null {
  const [laid, setLaid] = useState<Laid | null>(null)
  useEffect(() => {
    if (graph === undefined) return
    let cancelled = false
    const ids = new Set(graph.nodes.map((n) => n.id))
    const edges: ElkExtendedEdge[] = []
    for (const n of graph.nodes) for (const input of n.inputs) if (ids.has(input)) edges.push({ id: `${input}->${n.id}`, sources: [input], targets: [n.id] })
    for (const c of graph.checks) for (const side of [c.a, c.b]) if (ids.has(side)) edges.push({ id: `${side}->${c.id}`, sources: [side], targets: [c.id] })
    const input: ElkNode = {
        id: 'root',
        layoutOptions: {
          'elk.algorithm': 'layered',
          'elk.direction': 'RIGHT',
          'elk.edgeRouting': 'ORTHOGONAL',
          'elk.layered.spacing.nodeNodeBetweenLayers': '56',
          'elk.spacing.nodeNode': '12',
          'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
        },
        children: [
          ...graph.nodes.map((n) => ({ id: n.id, width: NODE_W, height: NODE_H })),
          ...graph.checks.map((c) => ({ id: c.id, width: NODE_W, height: NODE_H })),
        ],
        edges,
    }
    void elk
      .layout(input)
      .then((result: ElkNode) => {
        if (cancelled) return
        const checkIds = new Set(graph.checks.map((c) => c.id))
        setLaid({
          nodes: (result.children ?? []).map((c) => ({ id: c.id, x: c.x ?? 0, y: c.y ?? 0, kind: checkIds.has(c.id) ? 'check' : 'node' })),
          edges: (result.edges ?? []).map((e) => {
            const s = e.sections?.[0]
            const pts: [number, number][] = s ? [[s.startPoint.x, s.startPoint.y], ...(s.bendPoints ?? []).map((b) => [b.x, b.y] as [number, number]), [s.endPoint.x, s.endPoint.y]] : []
            return { id: e.id, points: pts }
          }),
          width: result.width ?? 0,
          height: result.height ?? 0,
        })
      })
    return () => {
      cancelled = true
    }
  }, [graph])
  return laid
}

function chainOf(graph: EvaluatedGraph, id: string): NodeResult[] {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]))
  const out: NodeResult[] = []
  const seen = new Set<string>()
  const visit = (nid: string) => {
    if (seen.has(nid)) return
    seen.add(nid)
    const n = byId.get(nid)
    if (n === undefined) return
    n.inputs.forEach(visit)
    out.push(n)
  }
  visit(id)
  return out
}

function GraphView({ graph, onPick, picked }: { graph: EvaluatedGraph; onPick: (id: string) => void; picked: string | null }) {
  const palette = usePalette()
  const laid = useLayout(graph)
  const [zoom, setZoom] = useState(0.8)
  const nodes = useMemo(() => new Map(graph.nodes.map((n) => [n.id, n])), [graph])
  const checks = useMemo(() => new Map(graph.checks.map((c) => [c.id, c])), [graph])
  if (palette === undefined) return null
  if (laid === null) return <Empty>Laying out the graph…</Empty>
  const color = (cls: string) => palette.classes.find((c) => c.key === cls)?.color ?? palette.muted
  return (
    <div className="graph-wrap">
      <div className="graph-zoom">
        <button type="button" className="icon-btn" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(z / 1.25, 0.25))}>
          <Minus size={14} />
        </button>
        <span className="small mono">{Math.round(zoom * 100)}%</span>
        <button type="button" className="icon-btn" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(z * 1.25, 2.5))}>
          <Plus size={14} />
        </button>
      </div>
      <div className="graph-scroll">
        <svg width={laid.width * zoom} height={laid.height * zoom} viewBox={`0 0 ${laid.width} ${laid.height}`} role="img" aria-label="Inference graph" data-testid="inference-graph">
          <g fill="none" stroke={palette.muted} strokeWidth={1}>
            {laid.edges.map((e) => (
              <polyline key={e.id} points={e.points.map((p) => p.join(',')).join(' ')} opacity={0.55} />
            ))}
          </g>
          {laid.nodes.map((n) => {
            const node = nodes.get(n.id)
            const check = checks.get(n.id)
            const status = check ? palette.status.find((s) => s.key === check.status) : undefined
            const stroke = check ? (status?.color ?? palette.muted) : color(node?.source_class ?? 'synthetic')
            const selected = picked === n.id
            return (
              <g key={n.id} transform={`translate(${n.x},${n.y})`} className="graph-node" onClick={() => onPick(n.id)} role="button" tabIndex={0} aria-label={n.id} onKeyDown={(e) => e.key === 'Enter' && onPick(n.id)}>
                <rect width={NODE_W} height={NODE_H} rx={check ? 18 : 4} fill={palette.surface} stroke={stroke} strokeWidth={selected ? 3 : 1.6} />
                <rect width={5} height={NODE_H} rx={2} fill={stroke} />
                <text x={11} y={15} fontSize={10.5} fill={palette.ink} fontFamily="ui-monospace, monospace">
                  {n.id.length > 30 ? `${n.id.slice(0, 29)}…` : n.id}
                </text>
                <text x={11} y={30} fontSize={10} fill={palette.muted}>
                  {check ? `${check.status} · gap ${num(check.gap_abs, 4)} ${check.unit}` : node?.nominal !== null && node?.nominal !== undefined ? `${num(node.nominal, 6)} ${node.unit}` : (node?.unit ?? '')}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}

function SupportMatrix({ graph }: { graph: EvaluatedGraph }) {
  const palette = usePalette()
  const checks = graph.checks.map((c) => c.id)
  if (palette === undefined) return null
  const sym: Record<string, string> = { CONSISTENT: '✓', TENSION: '!', CONFLICT: '✕' }
  return (
    <div className="matrix-scroll">
      <table className="matrix" data-testid="support-matrix">
        <thead>
          <tr>
            <th scope="col">hypothesis</th>
            {checks.map((c) => (
              <th key={c} scope="col" className="matrix-col">
                <span>{c.split('.').slice(1).join('.')}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {graph.support.map((row) => (
            <tr key={row.hypothesis}>
              <th scope="row">
                <Tip label={row.statement}>
                  <span>{row.hypothesis}</span>
                </Tip>
              </th>
              {checks.map((c) => {
                const cell = row.cells[c]
                const status = palette.status.find((s) => s.key === cell?.status)
                return (
                  <td key={c} style={{ background: status?.color }} title={`${row.hypothesis} × ${c}: ${cell?.status ?? ''}${cell?.gap_rel != null ? `, gap ${num(cell.gap_rel * 100, 3)} %` : ''}`}>
                    {cell ? sym[cell.status] : ''}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Tornado({ graph }: { graph: EvaluatedGraph }) {
  const palette = usePalette()
  const entries = graph.tornado.filter((t) => t.bars.length > 0)
  const [node, setNode] = useState<string>('')
  const entry = entries.find((t) => t.node === node) ?? entries[0]
  if (palette === undefined) return null
  if (entry === undefined) return <Empty>No assumption moves a derived value in this product.</Empty>
  const bars = [...entry.bars].sort((a, b) => a.swing - b.swing)
  return (
    <div className="tornado">
      <select value={entry.node} onChange={(e) => setNode(e.target.value)} aria-label="Derived node">
        {entries.map((t) => (
          <option key={t.node} value={t.node}>
            {t.node}
          </option>
        ))}
      </select>
      <Plot
        data={[
          {
            type: 'bar',
            orientation: 'h',
            y: bars.map((b) => b.assumption),
            x: bars.map((b) => b.value_at_low - entry.nominal),
            base: entry.nominal,
            name: 'at low',
            marker: { color: palette.classes.find((c) => c.key === 'synthetic')?.color },
            hovertemplate: '%{y} at low: %{x:+.4g}<extra></extra>',
          },
          {
            type: 'bar',
            orientation: 'h',
            y: bars.map((b) => b.assumption),
            x: bars.map((b) => b.value_at_high - entry.nominal),
            base: entry.nominal,
            name: 'at high',
            marker: { color: palette.classes.find((c) => c.key === 'inference')?.color },
            hovertemplate: '%{y} at high: %{x:+.4g}<extra></extra>',
          },
        ]}
        layout={baseLayout(palette, {
          barmode: 'overlay',
          margin: { l: 170, r: 16, t: 10, b: 36 },
          xaxis: { title: { text: `${entry.node} (nominal ${num(entry.nominal)})` } },
          shapes: [{ type: 'line', x0: entry.nominal, x1: entry.nominal, yref: 'paper', y0: 0, y1: 1, line: { color: palette.ink, width: 1 } }],
        })}
        config={PLOT_CONFIG}
        useResizeHandler
        style={{ width: '100%', height: 220 }}
      />
    </div>
  )
}

function Conflicts({ graph, references }: { graph: EvaluatedGraph; references: Map<string, BibEntry> | undefined }) {
  if (graph.conflicts.length === 0) return <Empty>No recorded conflicts.</Empty>
  const link = (cite: string) => {
    const url = references?.get(cite)?.url
    return url ? (
      <a href={url} target="_blank" rel="noreferrer" className="cite">
        {cite}
      </a>
    ) : (
      <span className="cite">{cite}</span>
    )
  }
  return (
    <div className="conflicts">
      {graph.conflicts.map((c) => (
        <article key={`${c.a}|${c.b}`} className="conflict" data-testid="conflict">
          <div className="conflict-side">
            <div className="small muted">{c.quantity_a}</div>
            <div className="conflict-value">{c.value_a}</div>
            <blockquote>“{c.quote_a}”</blockquote>
            <code>{c.a}</code> {link(c.cite_a)}
          </div>
          <div className="conflict-vs">
            <StatusBadge status="CONFLICT" />
          </div>
          <div className="conflict-side">
            <div className="small muted">{c.quantity_b}</div>
            <div className="conflict-value">{c.value_b}</div>
            <blockquote>“{c.quote_b}”</blockquote>
            <code>{c.b}</code> {link(c.cite_b)}
          </div>
        </article>
      ))}
    </div>
  )
}

export default function Inference({ product }: { product: ProductView | undefined }) {
  const references = useReferences().data
  const hypotheses = useExplorer((s) => s.hypotheses)
  const toggle = useExplorer((s) => s.toggleHypothesis)
  const [picked, setPicked] = useState<string | null>(null)
  if (product === undefined) return <Empty>This tab shows the inference graph of a catalog scene's product.</Empty>
  const graph = product.graph
  const groups = new Map(product.product.hypotheses.map((h) => [h.id, h.group]))
  const chain = picked ? chainOf(graph, picked) : []
  const check = picked ? graph.checks.find((c) => c.id === picked) : undefined
  return (
    <div className="view view-inference">
      <div className="view-col view-side inference-side">
        <Section title="Hypotheses">
          {product.product.hypotheses.length === 0 && <p className="muted small">None for this product.</p>}
          {product.product.hypotheses.map((h) => (
            <label key={h.id} className="hyp">
              <input type="checkbox" checked={hypotheses.includes(h.id)} onChange={() => toggle(h.id, h.group, (id) => groups.get(id) ?? '')} data-testid={`hyp-${h.id}`} />
              <span>
                <strong>{h.id}</strong>
                {h.group && <span className="muted small"> ({h.group})</span>}
                <br />
                <span className="small">{h.statement}</span>
              </span>
            </label>
          ))}
        </Section>
        {picked && (
          <Section title="Derivation chain">
            {check && (
              <div className="live-value">
                <StatusBadge status={check.status} />
                <span className="small">{check.explanation}</span>
              </div>
            )}
            {(check ? [...chainOf(graph, check.a), ...chainOf(graph, check.b)] : chain).map((n) => (
              <NodeCard key={n.id} node={n} references={references} />
            ))}
          </Section>
        )}
      </div>
      <div className="view-col view-wide">
        <div className="legend-row">
          {['fact', 'assumption', 'derived'].map((k) => (
            <span key={k} className="small muted">
              {k}s: {graph.nodes.filter((n) => n.kind === k).length}
            </span>
          ))}
          <span className="small muted">checks: {graph.checks.length}</span>
          {['vendor_claim', 'published_spec', 'peer_reviewed', 'third_party', 'proposed_standard', 'synthetic', 'inference'].map((c) => (
            <ClassBadge key={c} cls={c} />
          ))}
        </div>
        <GraphView graph={graph} onPick={setPicked} picked={picked} />
        <Section title="Support matrix (hypothesis × check)">
          <SupportMatrix graph={graph} />
        </Section>
        <Section title="Tornado (assumptions over their ranges)">
          <Tornado graph={graph} />
        </Section>
        <Section title="Conflicts (both sources)">
          <Conflicts graph={graph} references={references} />
        </Section>
      </div>
    </div>
  )
}
