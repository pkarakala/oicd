import type { FeasibilityReport, Link } from './types'

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

export async function fetchProfile(name: string, signal?: AbortSignal): Promise<Link> {
  return readJson<Link>(await fetch(`${API_URL}/profiles/${encodeURIComponent(name)}`, { signal }))
}

export async function evaluateLink(link: Link, signal?: AbortSignal): Promise<FeasibilityReport> {
  const response = await fetch(`${API_URL}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(link),
    signal,
  })
  return readJson<FeasibilityReport>(response)
}
