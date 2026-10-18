// Display helpers only: formatting and lookups of values the API returned.

import type { FeasibilityReport, InputRecord, TracePoint } from './types'

export function fmt(value: number, digits = 4): string {
  // Avoid "-0.0000" for tiny negative values that round to zero.
  const text = value.toFixed(digits)
  return /^-0\.?0*$/.test(text) ? text.slice(1) : text
}

/** Input records that describe a trace point: TX inputs at TP2, RX inputs at TP3, otherwise the
 * loss element's own record. */
export function inputsFor(report: FeasibilityReport, point: TracePoint): InputRecord[] {
  if (point.input_path !== null) return report.inputs.filter((r) => r.path === point.input_path)
  const prefix = point.name === 'TP2' ? 'tx.' : point.name === 'TP3' ? 'rx.' : null
  return prefix === null ? [] : report.inputs.filter((r) => r.path.startsWith(prefix))
}

/** At TP3 the threshold is S_RX + ΣΠ + R, so its panel also lists the penalty and reserve
 * records (review R3). Empty for every other point. */
export function thresholdTermsFor(report: FeasibilityReport, point: TracePoint): InputRecord[] {
  if (point.kind !== 'reference_plane' || point.name !== 'TP3') return []
  return report.inputs.filter((r) => r.path.startsWith('penalties[') || r.path === 'reserve')
}

/** Index of the trace point a selection key names, or null when it names none or several.
 * Keys are point names ("TP2", "TP3" or the element name), which survive a connector insert;
 * input paths do not, because they carry the channel index (review R5). */
export function indexForKey(report: FeasibilityReport, key: string | null): number | null {
  if (key === null) return null
  const matches = report.power_trace.flatMap((p, i) => (p.name === key ? [i] : []))
  return matches.length === 1 ? (matches[0] ?? null) : null
}

/** The one record shown in a hover tooltip: the loss, or the launch/sensitivity at a plane. */
export function primaryInput(report: FeasibilityReport, point: TracePoint): InputRecord | undefined {
  const all = inputsFor(report, point)
  if (point.name === 'TP2') return all.find((r) => r.path === 'tx.launch_oma_min')
  if (point.name === 'TP3') return all.find((r) => r.path === 'rx.sensitivity_oma_max')
  return all[0]
}

export function displayName(report: FeasibilityReport, point: TracePoint): string {
  if (point.name === 'TP2') return `${report.inputs.find((r) => r.path.startsWith('tx.'))?.name ?? 'TX'} (TP2)`
  if (point.name === 'TP3') return `${report.inputs.find((r) => r.path.startsWith('rx.'))?.name ?? 'RX'} (TP3)`
  return point.name
}
