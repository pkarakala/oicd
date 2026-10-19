// Physics: the product's engine evaluations (twin physics sections), each item with its class,
// sections under a hypothesis marked, verdicts with their status.

import type { ProductView } from '../api/client'
import { num } from '../lib/format'
import { ClassBadge, Empty, StatusBadge } from '../shell/ui'

export default function Physics({ product }: { product: ProductView | undefined }) {
  if (product === undefined) return <Empty>This tab shows the physics of a catalog scene's product.</Empty>
  const physics = product.physics
  if (physics === null) return <Empty>No physics evaluation applies to {product.product.name}; see the Inference tab.</Empty>
  return (
    <div className="view view-physics" data-testid="physics">
      <div className="physics-grid">
        {physics.sections.map((s, i) => (
          <section key={`${s.title}-${i}`} className="physics-section">
            <header className="physics-head">
              <h3>{s.title}</h3>
              {s.hypothesis && <span className="chip">{s.hypothesis}</span>}
              {s.verdict && <StatusBadge status={s.verdict} />}
            </header>
            <table className="physics-table">
              <tbody>
                {s.items.map((item, k) => (
                  <tr key={`${item.label}-${k}`}>
                    <td>{item.label}</td>
                    <td className="mono">
                      {typeof item.value === 'number' ? num(item.value) : (item.value ?? '—')} {item.unit}
                    </td>
                    <td>
                      <ClassBadge cls={item.source_class} />
                    </td>
                    {item.note && <td className="small muted">{item.note}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
            {s.note && <p className="small muted">{s.note}</p>}
          </section>
        ))}
      </div>
    </div>
  )
}
