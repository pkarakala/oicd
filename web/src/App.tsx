import { useEffect, useRef, useState } from 'react'
import { evaluateLink, fetchProfile } from './api'
import { Controls } from './components/Controls'
import { ChecksPanel, ProvenancePanel } from './components/Panels'
import { type CameraPreset, Scene3D } from './components/Scene3D'
import { Waterfall } from './components/Waterfall'
import { fmt, indexForKey } from './format'
import type { FeasibilityReport, Link } from './types'

const DEBOUNCE_MS = 150
const START_PROFILE = 'worked_example'

export default function App() {
  const [link, setLink] = useState<Link | null>(null)
  const [report, setReport] = useState<FeasibilityReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [hovered, setHovered] = useState<number | null>(null)
  // Selection is a stable key (the trace point's name), not an index, so inserting a connector
  // never moves an open panel to another component (review R5).
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [preset, setPreset] = useState<CameraPreset>('overview')
  const requestId = useRef(0)

  useEffect(() => {
    const controller = new AbortController()
    fetchProfile(START_PROFILE, controller.signal)
      .then(setLink)
      .catch((e: unknown) => {
        if (!controller.signal.aborted) setError(`Could not load profile: ${String(e)}`)
      })
    return () => controller.abort()
  }, [])

  // Every edit POSTs the whole Link, debounced; only the newest response is applied.
  useEffect(() => {
    if (link === null) return
    const id = ++requestId.current
    const controller = new AbortController()
    setPending(true)
    const timer = window.setTimeout(() => {
      evaluateLink(link, controller.signal)
        .then((next) => {
          if (id !== requestId.current) return
          setReport(next)
          setError(null)
        })
        .catch((e: unknown) => {
          if (id !== requestId.current || controller.signal.aborted) return
          setError(e instanceof Error ? e.message : String(e))
        })
        .finally(() => {
          if (id === requestId.current) setPending(false)
        })
    }, DEBOUNCE_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [link])

  const selected = report === null ? null : indexForKey(report, selectedKey)
  const select = (index: number | null) =>
    setSelectedKey(index === null || report === null ? null : (report.power_trace[index]?.name ?? null))
  // Drop a key that no longer names exactly one point.
  useEffect(() => {
    if (report !== null && selectedKey !== null && indexForKey(report, selectedKey) === null) setSelectedKey(null)
  }, [report, selectedKey])

  return (
    <div className="app">
      <header>
        <div>
          <h1>OICD link explorer</h1>
          <span className="muted">{report?.link_name ?? 'loading…'}</span>
        </div>
        {report && (
          <div className={`status-pill ${report.verdict === 'EXCLUDED' ? 'bad' : 'good'}`}>
            <span data-testid="verdict">{report.verdict}</span>
            <span>
              margin <span data-testid="margin">{fmt(report.margin_db)}</span> dB
            </span>
            {pending && <span className="muted"> · updating</span>}
          </div>
        )}
      </header>

      {error && (
        <div className="error" role="alert">
          Engine rejected the input or is unreachable: {error}
        </div>
      )}

      <main>
        {link && <Controls link={link} onChange={setLink} />}

        <div className="center">
          <div className="scene">
            <div className="presets" role="group" aria-label="Camera presets">
              {(['overview', 'tx', 'rx'] as const).map((p) => (
                <button key={p} type="button" className={preset === p ? 'active' : ''} onClick={() => setPreset(p)}>
                  {p === 'overview' ? 'Overview' : p === 'tx' ? 'TX close-up' : 'RX close-up'}
                </button>
              ))}
            </div>
            {report && (
              <Scene3D
                report={report}
                hovered={hovered}
                selected={selected}
                preset={preset}
                onHover={setHovered}
                onSelect={select}
              />
            )}
          </div>
          <div className="chart">
            {report && <Waterfall report={report} hovered={hovered} onHover={setHovered} />}
          </div>
          {report && <ChecksPanel report={report} />}
        </div>

        {report && selected !== null && (
          <ProvenancePanel report={report} index={selected} onClose={() => setSelectedKey(null)} />
        )}
      </main>

      <footer>Schematic, not to scale. Values synthetic unless cited. PASS means not excluded by modeled constraints.</footer>
    </div>
  )
}
