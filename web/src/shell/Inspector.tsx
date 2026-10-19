// Inspector: the selection's dimensions with their classes, material, function, live physics from
// the overlay, and the catalog nodes behind it with provenance and source links. In the link scene
// it shows the provenance panel for the selected trace point.

import { ArrowDownRight, Crosshair } from 'lucide-react'
import type { BibEntry, FeasibilityReport, InputRecord, NodeResult, Overlay, Part, SceneView } from '../api/client'
import { useCatalog, useReferences } from '../api/hooks'
import { displayName, formatLength, indexForKey, inputsFor, num, thresholdTermsFor } from '../lib/format'
import { useExplorer } from '../state/store'
import { enterScene } from './navigation'
import { ClassBadge, DimsBadge, Empty, IconButton, Section, StatusBadge, usePalette } from './ui'

function value(n: NodeResult): string {
  if (n.nominal === null) return n.label
  const unit = n.unit === '1' || n.unit === 'count' || n.unit === 'text' ? '' : ` ${n.unit}`
  const interval = n.lo !== null && n.hi !== null && (n.lo !== n.nominal || n.hi !== n.nominal) ? ` (${num(n.lo)} to ${num(n.hi)})` : ''
  return `${num(n.nominal)}${unit}${interval}`
}

function Cite({ cite, references }: { cite: string; references: Map<string, BibEntry> | undefined }) {
  const entry = references?.get(cite)
  return entry?.url ? (
    <a className="cite" href={entry.url} target="_blank" rel="noreferrer" title={entry.title}>
      {cite}
    </a>
  ) : (
    <span className="cite" title={entry?.title}>
      {cite}
    </span>
  )
}

export function NodeCard({ node, references }: { node: NodeResult; references: Map<string, BibEntry> | undefined }) {
  return (
    <article className="node-card" data-testid={`node-${node.id}`}>
      <header className="node-head">
        <span className="node-label">{node.kind === 'derived' ? node.label : node.label}</span>
        <ClassBadge cls={node.source_class} />
      </header>
      <div className="node-value">{value(node)}</div>
      <div className="node-derivation">{node.derivation}</div>
      {node.quote && <blockquote className="node-quote">“{node.quote}”</blockquote>}
      <footer className="node-foot">
        <code>{node.id}</code>
        {node.cite && <Cite cite={node.cite} references={references} />}
        {node.verified === false && <span className="node-unverified">not verified</span>}
        {node.pinned_by && <span className="node-pinned">pinned by {node.pinned_by}</span>}
      </footer>
    </article>
  )
}

const AXES = ['W (x)', 'D (y)', 'H (z)'] as const

function Dimensions({ part, unit }: { part: Part; unit: SceneView['scene']['scene']['unit'] }) {
  const axes = part.dims_axes ?? [part.dims_class, part.dims_class, part.dims_class]
  const rows: [string, number, string][] =
    part.shape === 'ring'
      ? [
          ['diameter', part.size[0], axes[0]],
          ['wall', part.wall ?? 0, 'SCHEMATIC'],
          ['height', part.size[2], axes[2]],
        ]
      : part.shape === 'tube' || part.shape === 'cylinder'
        ? [
            ['diameter', part.size[0], axes[0]],
            ...(part.shape === 'cylinder' ? ([['length', part.size[2], axes[2]]] as [string, number, string][]) : []),
          ]
        : AXES.map((label, i) => [label, part.size[i] ?? 0, axes[i] ?? part.dims_class])
  return (
    <table className="dims" data-testid="dims-table">
      <tbody>
        {rows.map(([label, size, cls]) => (
          <tr key={label}>
            <th scope="row">{label}</th>
            <td className="mono">{formatLength(size, unit, 5)}</td>
            <td>
              <DimsBadge cls={cls} />
            </td>
          </tr>
        ))}
        {part.count > 1 && (
          <tr>
            <th scope="row">instances</th>
            <td className="mono" colSpan={2}>
              {part.count} ({part.grid.join(' × ')}), pitch {part.pitch.filter((p) => p > 0).map((p) => formatLength(p, unit, 4)).join(' × ') || '—'}
            </td>
          </tr>
        )}
      </tbody>
    </table>
  )
}

function LivePhysics({ part, overlay }: { part: Part; overlay: Overlay | undefined }) {
  const value = overlay?.values.find((v) => v.part === part.id)
  const paths = overlay?.paths.filter((p) => p.part === part.id) ?? []
  if (value === undefined && paths.length === 0) return null
  return (
    <Section title="Live physics (API)">
      {value && (
        <div className="live-value" data-testid="live-value">
          {value.verdict && <StatusBadge status={value.verdict} />}
          {value.color && <span className="chip-dot" style={{ background: value.color }} aria-hidden />}
          <span>{value.label}</span>
          <ClassBadge cls={value.source_class} />
        </div>
      )}
      {paths.map((p, i) => {
        const first = p.samples[0]
        const last = p.samples[p.samples.length - 1]
        return (
          <div key={i} className="live-path">
            <span className="legend-swatch" style={{ background: p.color }} aria-hidden />
            <span>
              {p.kind === 'ghost' ? 'ghost: ' : ''}
              {p.label}
              {first?.power_mw != null && last?.power_mw != null && (
                <span className="muted">
                  {' '}
                  · {num(first.power_mw, 5)} → {num(last.power_mw, 5)} mW {p.power_kind ?? ''}
                </span>
              )}
            </span>
            <ClassBadge cls={p.source_class} />
          </div>
        )
      })}
    </Section>
  )
}

function PartInspector({ part, view, overlay }: { part: Part; view: SceneView; overlay: Overlay | undefined }) {
  const palette = usePalette()
  const references = useReferences().data
  const command = useExplorer((s) => s.command)
  const unit = view.scene.scene.unit
  const nodes = new Map(view.nodes.map((n) => [n.id, n]))
  const material = palette?.materials.find((m) => m.key === part.material)
  const source = nodes.get(part.dims_source)
  const shown = part.nodes.map((id) => nodes.get(id)).filter((n): n is NodeResult => n !== undefined)
  return (
    <div className="inspector-body" data-testid="inspector">
      <header className="insp-head">
        <div>
          <h2 className="insp-title">{part.name}</h2>
          <code className="insp-id">{part.id}</code>
          {part.assembly && <span className="insp-assembly"> · {part.assembly}</span>}
        </div>
        <div className="insp-actions">
          <IconButton label="Fit selection" shortcut="⇧F" onClick={() => command({ kind: 'fitSelection' })}>
            <Crosshair size={15} />
          </IconButton>
          {part.enters && (
            <button type="button" className="btn" onClick={() => enterScene(part.enters, part.id)} data-testid="enter-button">
              <ArrowDownRight size={14} /> Zoom in
            </button>
          )}
        </div>
      </header>
      <Section title="Dimensions" aside={<DimsBadge cls={part.dims_class} />}>
        <Dimensions part={part} unit={unit} />
        {source ? <NodeCard node={source} references={references} /> : <p className="muted small">{part.dims_source}</p>}
      </Section>
      {material && (
        <Section title="Material">
          <div className="material-row">
            <span className="material-swatch" style={{ background: material.color }} aria-hidden />
            <span>{material.label}</span>
            <span className="muted small">
              metalness {material.metalness}, roughness {material.roughness}
              {material.transmission > 0 ? `, transmission ${material.transmission}` : ''}
            </span>
          </div>
        </Section>
      )}
      {part.function && (
        <Section title="Function">
          <p>{part.function}</p>
        </Section>
      )}
      <LivePhysics part={part} overlay={overlay} />
      {shown.length > 0 && (
        <Section title="Catalog">
          {shown.map((n) => (
            <NodeCard key={n.id} node={n} references={references} />
          ))}
        </Section>
      )}
    </div>
  )
}

function SceneSummary({ view }: { view: SceneView }) {
  const catalog = useCatalog()
  const product = catalog.data?.products.find((p) => p.id === view.scene.scene.product)
  return (
    <div className="inspector-body">
      <h2 className="insp-title">{view.scene.scene.name}</h2>
      <p>{view.scene.scene.summary}</p>
      {product && (
        <Section title={product.name}>
          <p className="muted small">{product.summary}</p>
          <p className="small">
            {product.facts} facts ({product.verified_facts} verified) · {product.assumptions} assumptions ·{' '}
            {product.derived} derived · {product.checks} checks · {product.hypotheses.length} hypotheses
          </p>
          <p className="small muted">{product.status}</p>
        </Section>
      )}
      {view.source_issues.length > 0 && (
        <Section title="Source issues">
          <ul>
            {view.source_issues.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        </Section>
      )}
      <Empty>Click a part to inspect it; double-click a part marked ↘ to zoom into its level.</Empty>
    </div>
  )
}

function Record({ r }: { r: InputRecord }) {
  return (
    <dl className="record">
      <dt>path</dt>
      <dd>
        <code>{r.path}</code>
      </dd>
      <dt>value</dt>
      <dd>
        {String(r.value)} {r.unit}
      </dd>
      <dt>source class</dt>
      <dd>
        <ClassBadge cls={r.source_class} />
      </dd>
      <dt>citation key</dt>
      <dd>{r.citation_key ?? 'none'}</dd>
      <dt>rationale</dt>
      <dd>{r.rationale}</dd>
    </dl>
  )
}

/** The provenance panel: inputs behind a trace point, with the threshold terms at TP3. */
export function ProvenancePanel({ report, index, onClose }: { report: FeasibilityReport; index: number; onClose: () => void }) {
  const point = report.power_trace[index]
  if (point === undefined) return null
  const terms = thresholdTermsFor(report, point)
  return (
    <aside className="inspector-body provenance" aria-label="Provenance">
      <div className="provenance-head">
        <h2 className="insp-title">{displayName(report, point)}</h2>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close provenance">
          ×
        </button>
      </div>
      <p className="muted small">
        {point.kind === 'reference_plane' ? 'Reference plane' : 'Channel element'} · OMA here {point.power_dbm} dBm ·
        headroom {point.headroom_db} dB · {num(point.power_mw, 6)} mW
      </p>
      {inputsFor(report, point).map((r) => (
        <Record key={r.path} r={r} />
      ))}
      {terms.length > 0 && (
        <section aria-label="Threshold terms">
          <h3>Threshold terms</h3>
          <p className="muted small">threshold {report.threshold_dbm} dBm OMA = sensitivity + penalties + reserve</p>
          {terms.map((r) => (
            <Record key={r.path} r={r} />
          ))}
        </section>
      )}
    </aside>
  )
}

export function Inspector({ view, overlay, report }: { view: SceneView | undefined; overlay: Overlay | undefined; report: FeasibilityReport | undefined }) {
  const selection = useExplorer((s) => s.selection)
  const select = useExplorer((s) => s.select)
  if (view === undefined) {
    if (report === undefined) return <aside className="inspector" aria-label="Inspector"><Empty>Waiting for the engine…</Empty></aside>
    const index = indexForKey(report, selection)
    return (
      <aside className="inspector" aria-label="Inspector">
        <div className="pane-title">Inspector</div>
        {index === null ? <Empty>Click a link element to see where its numbers come from.</Empty> : <ProvenancePanel report={report} index={index} onClose={() => select(null)} />}
      </aside>
    )
  }
  const part = view.scene.part.find((p) => p.id === selection)
  return (
    <aside className="inspector" aria-label="Inspector">
      <div className="pane-title">Inspector</div>
      {part ? <PartInspector part={part} view={view} overlay={overlay} /> : <SceneSummary view={view} />}
    </aside>
  )
}
