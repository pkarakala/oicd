// Model tree: assemblies and parts of the scene, with visibility, isolate and search. In the link
// scene it lists the trace points (TP2, each channel element, TP3).

import { Eye, EyeOff, Focus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { FeasibilityReport, Part, SceneView } from '../api/client'
import { dimsSwatch, displayName } from '../lib/format'
import { useExplorer } from '../state/store'
import { Empty, Tip, usePalette } from './ui'

function PartRow({ part }: { part: Part }) {
  const palette = usePalette()
  const selected = useExplorer((s) => s.selection === part.id)
  const hidden = useExplorer((s) => s.hidden.includes(part.id))
  const isolated = useExplorer((s) => s.isolated === part.id)
  const select = useExplorer((s) => s.select)
  const hover = useExplorer((s) => s.hover)
  const toggleHidden = useExplorer((s) => s.toggleHidden)
  const isolate = useExplorer((s) => s.isolate)
  const swatch = dimsSwatch(palette, part.dims_class)
  return (
    <li className={`tree-row ${selected ? 'is-selected' : ''} ${hidden ? 'is-hidden' : ''}`} onMouseEnter={() => hover(part.id)} onMouseLeave={() => hover(null)}>
      <button type="button" className="tree-eye" aria-label={hidden ? `Show ${part.name}` : `Hide ${part.name}`} onClick={() => toggleHidden(part.id)}>
        {hidden ? <EyeOff size={13} /> : <Eye size={13} />}
      </button>
      <button type="button" className="tree-name" aria-pressed={selected} onClick={() => select(part.id)} title={part.id}>
        <span className="tree-dot" style={{ background: swatch?.color }} title={swatch?.label} aria-hidden />
        <span className="tree-label">{part.name}</span>
        {part.count > 1 && <span className="tree-count">×{part.count}</span>}
      </button>
      <Tip label={isolated ? 'Show everything' : 'Isolate'}>
        <button type="button" className={`tree-isolate ${isolated ? 'is-active' : ''}`} aria-label={isolated ? 'Show everything' : `Isolate ${part.name}`} onClick={() => isolate(isolated ? null : part.id)}>
          <Focus size={13} />
        </button>
      </Tip>
    </li>
  )
}

export function ModelTree({ view, report }: { view: SceneView | undefined; report: FeasibilityReport | undefined }) {
  const [query, setQuery] = useState('')
  const select = useExplorer((s) => s.select)
  const selection = useExplorer((s) => s.selection)
  const groups = useMemo(() => {
    const q = query.trim().toLowerCase()
    const out = new Map<string, Part[]>()
    for (const part of view?.scene.part ?? []) {
      const text = `${part.name} ${part.id} ${part.assembly}`.toLowerCase()
      if (q && !text.includes(q)) continue
      const key = part.assembly || 'parts'
      out.set(key, [...(out.get(key) ?? []), part])
    }
    return [...out.entries()]
  }, [view, query])

  if (report !== undefined) {
    return (
      <aside className="tree" aria-label="Model tree">
        <div className="pane-title">Link elements</div>
        <ul className="tree-list">
          {report.power_trace.map((p) => (
            <li key={p.name} className={`tree-row ${selection === p.name ? 'is-selected' : ''}`}>
              <button type="button" className="tree-name" onClick={() => select(p.name)} aria-pressed={selection === p.name}>
                <span className="tree-label">{displayName(report, p)}</span>
                <span className="tree-count">{p.kind === 'reference_plane' ? 'plane' : `${p.loss_db} dB`}</span>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    )
  }
  return (
    <aside className="tree" aria-label="Model tree">
      <div className="pane-title">Model</div>
      <label className="tree-search">
        <Search size={13} aria-hidden />
        <input type="search" placeholder="Search parts" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search parts" />
      </label>
      {view === undefined && <Empty>Loading the scene…</Empty>}
      {groups.map(([assembly, parts]) => (
        <section key={assembly} className="tree-group">
          <div className="tree-assembly">{assembly}</div>
          <ul className="tree-list">
            {parts.map((part) => (
              <PartRow key={part.id} part={part} />
            ))}
          </ul>
        </section>
      ))}
      {view !== undefined && groups.length === 0 && <Empty>No part matches “{query}”.</Empty>}
    </aside>
  )
}
