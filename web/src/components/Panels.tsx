import { displayName, inputsFor, thresholdTermsFor } from '../format'
import type { CheckResult, FeasibilityReport, InputRecord } from '../types'

function Record({ r }: { r: InputRecord }) {
  return (
    <dl>
      <dt>path</dt>
      <dd>
        <code>{r.path}</code>
      </dd>
      <dt>value</dt>
      <dd>
        {String(r.value)} {r.unit}
      </dd>
      <dt>source class</dt>
      <dd>{r.source_class}</dd>
      <dt>citation key</dt>
      <dd>{r.citation_key ?? 'none'}</dd>
      <dt>rationale</dt>
      <dd>{r.rationale}</dd>
    </dl>
  )
}

function Result({ result }: { result: CheckResult }) {
  return (
    <li className={`result result-${result.status}`}>
      <div>
        <span className="status">{result.status.toUpperCase()}</span> <code>{result.constraint}</code>
      </div>
      <div className="muted">{result.message}</div>
    </li>
  )
}

export function ChecksPanel({ report }: { report: FeasibilityReport }) {
  return (
    <details className="panel checks" open>
      <summary>Checks ({report.results.length} evaluated, {report.not_evaluated.length} not evaluated)</summary>
      <ul>
        {report.results.map((r) => (
          <Result key={r.constraint} result={r} />
        ))}
      </ul>
      <h3>Not evaluated</h3>
      <ul>
        {report.not_evaluated.map((r) => (
          <Result key={r.constraint} result={r} />
        ))}
      </ul>
    </details>
  )
}

export function ProvenancePanel({
  report,
  index,
  onClose,
}: {
  report: FeasibilityReport
  index: number
  onClose: () => void
}) {
  const point = report.power_trace[index]
  if (point === undefined) return null
  return (
    <aside className="panel provenance" aria-label="Provenance">
      <div className="provenance-head">
        <h2>{displayName(report, point)}</h2>
        <button type="button" onClick={onClose} aria-label="Close provenance">
          ×
        </button>
      </div>
      <p className="muted">
        {point.kind === 'reference_plane' ? 'Reference plane' : 'Channel element'} · OMA here {point.power_dbm} dBm ·
        headroom {point.headroom_db} dB
      </p>
      {inputsFor(report, point).map((r) => (
        <Record key={r.path} r={r} />
      ))}
      {thresholdTermsFor(report, point).length > 0 && (
        <section aria-label="Threshold terms">
          <h3>Threshold terms</h3>
          <p className="muted">threshold {report.threshold_dbm} dBm OMA = sensitivity + penalties + reserve</p>
          {thresholdTermsFor(report, point).map((r) => (
            <Record key={r.path} r={r} />
          ))}
        </section>
      )}
    </aside>
  )
}
