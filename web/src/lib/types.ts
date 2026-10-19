// Re-exports of generated API types used by the display helpers.
export type {
  FeasibilityReport,
  InputRecord,
  Palette,
  SceneInfo,
  TracePoint,
} from '../api/client'

export interface MarginBinLike {
  lo_db: number | null
  hi_db: number | null
  color: string
}
