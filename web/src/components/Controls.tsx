import { useEffect, useState } from 'react'
import { addConnector, setLaunch, setLoss, setPenalty, setReserve, setSensitivity } from '../linkEdits'
import type { Link } from '../types'

interface SliderProps {
  label: string
  unit: string
  value: number
  min: number
  max: number
  onChange: (value: number) => void
}

/** Slider plus a number box. The slider range is a UI convenience; the number box accepts any
 * value and the engine decides whether it is valid physics. */
function Slider({ label, unit, value, min, max, onChange }: SliderProps) {
  const [text, setText] = useState(String(value))
  useEffect(() => setText(String(value)), [value])
  const commit = (raw: string) => {
    setText(raw)
    const parsed = Number(raw)
    if (raw.trim() !== '' && Number.isFinite(parsed)) onChange(parsed)
  }
  return (
    <div className="slider">
      <div className="slider-head">
        <span>{label}</span>
        <span className="slider-value">
          <input
            type="number"
            step="any"
            aria-label={`${label} (${unit})`}
            value={text}
            onChange={(e) => commit(e.target.value)}
          />
          {unit}
        </span>
      </div>
      <input
        type="range"
        step="any"
        min={min}
        max={max}
        aria-label={`${label} slider`}
        value={Math.min(Math.max(value, min), max)}
        onChange={(e) => commit(e.target.value)}
      />
    </div>
  )
}

export function Controls({ link, onChange }: { link: Link; onChange: (link: Link) => void }) {
  return (
    <section className="panel controls" aria-label="Controls">
      <h2>Inputs</h2>
      <h3>Transmitter and receiver</h3>
      <Slider
        label="TX launch OMA"
        unit="dBm"
        value={link.tx.launch_oma_min.value.power_dbm.value}
        min={-10}
        max={6}
        onChange={(v) => onChange(setLaunch(link, v))}
      />
      <Slider
        label="RX sensitivity OMA"
        unit="dBm"
        value={link.rx.sensitivity_oma_max.value.power_dbm.value}
        min={-14}
        max={0}
        onChange={(v) => onChange(setSensitivity(link, v))}
      />
      <h3>Channel (TP2 to TP3)</h3>
      {link.channel.map((element, i) => (
        <Slider
          key={`${i}-${element.name}`}
          label={`${element.name} loss`}
          unit="dB"
          value={element.loss_max.value.value}
          min={0}
          max={6}
          onChange={(v) => onChange(setLoss(link, i, v))}
        />
      ))}
      <button type="button" onClick={() => onChange(addConnector(link))}>
        Add connector
      </button>
      <h3>Penalties and reserve</h3>
      {link.penalties.length === 0 && <p className="muted">No named penalties in this link.</p>}
      {link.penalties.map((penalty, i) => (
        <Slider
          key={`${i}-${penalty.name}`}
          label={`${penalty.name} penalty`}
          unit="dB"
          value={penalty.value.value.value}
          min={0}
          max={5}
          onChange={(v) => onChange(setPenalty(link, i, v))}
        />
      ))}
      <Slider
        label="Reserve"
        unit="dB"
        value={link.reserve.value.value}
        min={0}
        max={5}
        onChange={(v) => onChange(setReserve(link, v))}
      />
    </section>
  )
}
