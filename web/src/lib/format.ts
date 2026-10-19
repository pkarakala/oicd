// Display helpers only: formatting and lookups of values the API returned. No physics.

import type {
  FeasibilityReport,
  InputRecord,
  MarginBinLike,
  Palette,
  SceneInfo,
  TracePoint,
} from './types'

export function fmt(value: number, digits = 4): string {
  // Avoid "-0.0000" for tiny negative values that round to zero.
  const text = value.toFixed(digits)
  return /^-0\.?0*$/.test(text) ? text.slice(1) : text
}

/** A number as the engine would print it: up to 7 significant digits, true minus sign. */
export function num(value: number, digits = 7): string {
  if (!Number.isFinite(value)) return String(value)
  const text = Number(value.toPrecision(digits)).toString()
  return text.startsWith('-') ? `−${text.slice(1)}` : text
}

export function signed(value: number, digits = 4): string {
  const text = fmt(value, digits)
  return text.startsWith('-') ? `−${text.slice(1)}` : `+${text}`
}

const UNIT_TO_M: Record<SceneInfo['unit'], number> = { m: 1, mm: 1e-3, um: 1e-6, nm: 1e-9 }
export const UNIT_LABEL: Record<SceneInfo['unit'], string> = { m: 'm', mm: 'mm', um: 'µm', nm: 'nm' }

/** A length given in scene units, in the unit that suits it (m, mm, µm or nm). */
export function formatLength(value: number, sceneUnit: SceneInfo['unit'], digits = 4): string {
  if (value === 0) return `0 ${UNIT_LABEL[sceneUnit]}`
  const meters = Math.abs(value) * UNIT_TO_M[sceneUnit]
  const [factor, label] =
    meters >= 1 ? [1, 'm'] : meters >= 1e-3 ? [1e3, 'mm'] : meters >= 1e-6 ? [1e6, 'µm'] : [1e9, 'nm']
  return `${num(value * UNIT_TO_M[sceneUnit] * factor, digits)} ${label}`
}

/** The largest 1, 2 or 5 × 10^k not above `limit` (scale bar and grid steps). */
export function niceStep(limit: number): number {
  if (!(limit > 0)) return 1
  const power = 10 ** Math.floor(Math.log10(limit))
  for (const m of [5, 2, 1]) if (m * power <= limit) return m * power
  return power
}

export function classSwatch(palette: Palette | undefined, key: string) {
  return palette?.classes.find((c) => c.key === key)
}

export function dimsSwatch(palette: Palette | undefined, key: string) {
  return palette?.dims_classes.find((c) => c.key === key)
}

export function statusSwatch(palette: Palette | undefined, key: string) {
  return palette?.status.find((c) => c.key === key)
}

/** The color of the API bin that holds a margin (the engine defines the bins). */
export function marginColor(bins: readonly MarginBinLike[], value: number): string | undefined {
  return bins.find((b) => (b.lo_db === null || value >= b.lo_db) && (b.hi_db === null || value < b.hi_db))?.color
}

// --- the brief 03 link view ------------------------------------------------------------------

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
