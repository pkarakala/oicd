// Typed access to the engine API. Types come from the generated OpenAPI schema (npm run gen:api);
// the web only displays what these endpoints return.

import type { components } from './schema'

type S = components['schemas']
export type Palette = S['Palette']
export type Material = S['Material']
export type SceneList = S['SceneList']
export type SceneInfo = S['SceneInfo']
export type SceneView = S['SceneView']
export type Part = S['Part']
export type NodeResult = S['NodeResult']
export type CheckOutcome = S['CheckOutcome']
export type Caption = S['Caption']
export type Overlay = S['Overlay']
export type LightPath = S['LightPath']
export type PartValue = S['PartValue']
export type CatalogIndex = S['CatalogIndex']
export type ProductSummary = S['ProductSummary']
export type ProductView = S['ProductView']
export type EvaluatedGraph = S['EvaluatedGraph']
export type SupportRow = S['SupportRow']
export type TornadoEntry = S['TornadoEntry']
export type ConflictPair = S['ConflictPair']
export type Section = S['Section']
export type Link = S['Link']
export type FeasibilityReport = S['FeasibilityReport']
export type TracePoint = S['TracePoint']
export type InputRecord = S['InputRecord']
export type CheckResult = S['CheckResult']
export type SweepResult = S['SweepResult']
export type TrayReport = S['TrayReport']
export type YieldResponse = S['YieldResponse']
export type CrosstalkResponse = S['CrosstalkResponse']
export type SpectrumView = S['SpectrumView']
export type PtcSimulateRequest = S['PtcSimulateRequest']
export type PtcSimulateResponse = S['PtcSimulateResponse']
export type Grid = S['Grid']
export type BibEntry = S['BibEntry']
export type SourceClass = S['SourceClass']
export type DimsClass = Part['dims_class']
export type Provenance = S['Provenance']

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // keep the status line
    }
    throw new ApiError(detail)
  }
  return (await response.json()) as T
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return readJson<T>(await fetch(`${API_URL}${path}`, { signal }))
}

export async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  return readJson<T>(response)
}

export function query(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}
