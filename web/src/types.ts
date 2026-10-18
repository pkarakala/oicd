// JSON shapes of the engine's Link (oicd.schema) and FeasibilityReport (oicd.report).
// The web app only displays these; it never computes dB, margins or verdicts.

export type SourceClass =
  | 'published_spec'
  | 'proposed_standard'
  | 'vendor_claim'
  | 'synthetic'
  | 'inference'

export interface Provenance {
  source_class: SourceClass
  citation_key: string | null
  rationale: string
}

export interface Quantity<T> {
  value: T
  provenance: Provenance
}

export interface DBValue {
  value: number
}

export interface OpticalPower {
  power_dbm: DBValue
  kind: 'oma' | 'average'
}

export interface ElectricalInterface {
  modulation: 'NRZ' | 'PAM4'
  symbol_rate_gbd: number
  lanes: number
  fec: string
  provenance: Provenance
}

export interface Transmitter {
  name: string
  electrical: ElectricalInterface
  center_wavelength_nm: Quantity<number>
  wavelength_tolerance_nm: Quantity<number>
  launch_oma_min: Quantity<OpticalPower>
}

export interface Receiver {
  name: string
  electrical: ElectricalInterface
  passband_min_nm: Quantity<number>
  passband_max_nm: Quantity<number>
  sensitivity_oma_max: Quantity<OpticalPower>
}

export interface LossElement {
  name: string
  loss_max: Quantity<DBValue>
}

export interface Penalty {
  name: string
  value: Quantity<DBValue>
}

export interface Link {
  name: string
  tx: Transmitter
  rx: Receiver
  channel: LossElement[]
  penalties: Penalty[]
  reserve: Quantity<DBValue>
}

export type Status = 'pass' | 'fail' | 'not_evaluated'

export interface CheckResult {
  constraint: string
  status: Status
  evidence: Record<string, number | string>
  message: string
}

export interface InputRecord {
  path: string
  name: string
  value: number | string
  unit: string
  source_class: SourceClass
  citation_key: string | null
  rationale: string
}

export interface TracePoint {
  kind: 'reference_plane' | 'loss_element'
  name: string
  channel_index: number | null
  input_path: string | null
  power_dbm: number
  loss_db: number | null
  loss_fraction: number | null
  headroom_db: number
}

export interface FeasibilityReport {
  link_name: string
  verdict: 'NOT_EXCLUDED' | 'EXCLUDED'
  margin_db: number
  threshold_dbm: number
  results: CheckResult[]
  not_evaluated: CheckResult[]
  inputs: InputRecord[]
  power_trace: TracePoint[]
}
