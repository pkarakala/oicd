// Spec sheet: the product's facts and assumptions as the catalog states them, each with its class,
// verification, quote and source link (GET /catalog/{product}).

import { useState } from 'react'
import type { NodeResult, ProductView } from '../api/client'
import { useReferences } from '../api/hooks'
import { num } from '../lib/format'
import { ClassBadge, Empty } from '../shell/ui'

function valueText(n: NodeResult): string {
  if (n.nominal === null) return '—'
  const unit = n.unit === '1' || n.unit === 'count' ? '' : ` ${n.unit}`
  const bound = n.bound === 'min' ? '≥ ' : n.bound === 'max' ? '≤ ' : n.bound === 'approx' ? '≈ ' : ''
  return `${bound}${num(n.nominal)}${unit}`
}

export default function SpecSheet({ product }: { product: ProductView | undefined }) {
  const references = useReferences().data
  const [chosen, setKind] = useState<'fact' | 'assumption' | 'derived' | null>(null)
  const [query, setQuery] = useState('')
  if (product === undefined) return <Empty>This tab shows the spec sheet of a catalog scene's product.</Empty>
  const mine = product.graph.nodes.filter((n) => n.file === product.product.id)
  // the first kind this product has (the reference rack has no facts)
  const kind = chosen ?? (['fact', 'assumption', 'derived'] as const).find((k) => mine.some((n) => n.kind === k)) ?? 'fact'
  const own = mine.filter((n) => n.kind === kind)
  const q = query.trim().toLowerCase()
  const rows = own.filter((n) => !q || `${n.id} ${n.label} ${n.quote ?? ''}`.toLowerCase().includes(q))
  return (
    <div className="view view-spec">
      <div className="spec-head">
        <strong>{product.product.name}</strong>
        <span className="muted small">
          {product.product.facts} facts ({product.product.verified_facts} verified), {product.product.assumptions} assumptions, {product.product.derived} derived
        </span>
        <div className="seg" role="tablist" aria-label="Node kind">
          {(['fact', 'assumption', 'derived'] as const).map((k) => (
            <button key={k} type="button" role="tab" aria-selected={kind === k} className={`seg-btn ${kind === k ? 'is-active' : ''}`} onClick={() => setKind(k)}>
              {k === 'fact' ? 'Facts' : k === 'assumption' ? 'Assumptions (SYNTHETIC)' : 'Derived (INFERENCE)'}
            </button>
          ))}
        </div>
        <input type="search" placeholder="Filter" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Filter the spec sheet" />
      </div>
      <div className="table-scroll">
        <table className="spec" data-testid="spec-sheet">
          <thead>
            <tr>
              <th>quantity</th>
              <th>value</th>
              <th>class</th>
              <th>{kind === 'fact' ? 'source' : kind === 'assumption' ? 'range and rationale' : 'derivation'}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((n) => {
              const entry = n.cite ? references?.get(n.cite) : undefined
              return (
                <tr key={n.id}>
                  <td>
                    <div>{n.label}</div>
                    <code className="small muted">{n.id}</code>
                  </td>
                  <td className="mono">{valueText(n)}</td>
                  <td>
                    <ClassBadge cls={n.source_class} />
                    {n.verified === false && <div className="node-unverified">not verified</div>}
                  </td>
                  <td className="small">
                    {kind === 'fact' ? (
                      <>
                        {n.quote && <span>“{n.quote}” </span>}
                        {n.cite &&
                          (entry?.url ? (
                            <a href={entry.url} target="_blank" rel="noreferrer" className="cite" title={entry.title}>
                              {n.cite}
                            </a>
                          ) : (
                            <span className="cite">{n.cite}</span>
                          ))}
                      </>
                    ) : (
                      n.derivation
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
