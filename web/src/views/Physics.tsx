// Physics: the product's engine evaluations (twin physics sections), each item with its class,
// sections under a hypothesis marked, verdicts with their status.

import { useState } from 'react'
import type { PtcSimulateRequest, ProductView } from '../api/client'
import { usePtcSimulate } from '../api/hooks'
import { fmt, num } from '../lib/format'
import { ClassBadge, Empty, StatusBadge } from '../shell/ui'
import { NumberSlider } from './LinkBudget'

/** POST /ptc/simulate: one seeded run of the ABFP data path (model card §15.3, §15.4). */
function PtcSimulator() {
  const [gain, setGain] = useState(1.86)
  const [enob, setEnob] = useState(9.8)
  const [length, setLength] = useState(128)
  const [scale, setScale] = useState<'abfp' | 'global'>('abfp')
  const [range, setRange] = useState<'n' | '1'>('n')
  const [distribution, setDistribution] = useState<'gaussian' | 'student_t'>('gaussian')
  const request: PtcSimulateRequest = {
    length,
    rows: 64,
    trials: 8,
    seed: 0,
    distribution,
    config: { gain, enob, scale, output_range: range, weight_bits: 7, activation_bits: 10, adc_bits: 11, block: 128, bfloat16_scales: true },
  }
  const result = usePtcSimulate(request, true)
  const r = result.data
  return (
    <section className="physics-section ptc-sim" data-testid="ptc-simulator">
      <header className="physics-head">
        <h3>ABFP data path simulator (POST /ptc/simulate)</h3>
        <ClassBadge cls="inference" />
      </header>
      <NumberSlider label="gain G" unit="" value={gain} min={0.1} max={64} onChange={setGain} />
      <NumberSlider label="ADC ENOB" unit="bits" value={enob} min={4} max={12} onChange={setEnob} />
      <NumberSlider label="vector length" unit="" value={length} min={128} max={1024} onChange={(v) => setLength(Math.max(1, Math.round(v)))} />
      <div className="seg-row">
        <select value={scale} onChange={(e) => setScale(e.target.value as 'abfp' | 'global')} aria-label="Scales">
          <option value="abfp">one scale per 128-block (ABFP)</option>
          <option value="global">one global scale</option>
        </select>
        <select value={range} onChange={(e) => setRange(e.target.value as 'n' | '1')} aria-label="ADC range reading">
          <option value="n">H_out_n: ADC spans ±n</option>
          <option value="1">H_out_1: SI clamp read literally</option>
        </select>
        <select value={distribution} onChange={(e) => setDistribution(e.target.value as 'gaussian' | 'student_t')} aria-label="Activations">
          <option value="gaussian">Gaussian activations</option>
          <option value="student_t">Student-t activations (outliers)</option>
        </select>
      </div>
      {r && (
        <dl className="kv">
          <dt>relative error</dt>
          <dd data-testid="ptc-error">{fmt(100 * r.relative_error, 3)} %</dd>
          <dt>effective bits</dt>
          <dd>{fmt(r.effective_bits, 2)}</dd>
          <dt>ADC samples clipped</dt>
          <dd>{fmt(100 * r.clipped_fraction, 2)} %</dd>
          <dt>hand case codes</dt>
          <dd>
            [{r.hand_cases[1].codes.join(', ')}] at scale {num(r.hand_cases[1].scale)} (bfloat16)
          </dd>
        </dl>
      )}
      {result.isError && <p className="small">{String(result.error)}</p>}
      <p className="muted small">{r?.label}</p>
    </section>
  )
}

export default function Physics({ product }: { product: ProductView | undefined }) {
  if (product === undefined) return <Empty>This tab shows the physics of a catalog scene's product.</Empty>
  const physics = product.physics
  if (physics === null) return <Empty>No physics evaluation applies to {product.product.name}; see the Inference tab.</Empty>
  return (
    <div className="view view-physics" data-testid="physics">
      <div className="physics-grid">
        {product.product.id === 'photonic_processor' && <PtcSimulator />}
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
