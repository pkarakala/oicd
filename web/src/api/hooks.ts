// React Query hooks over the engine API. Every request is keyed by its full input, so the
// newest input's response is the one shown (stale responses never overwrite newer ones).

import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import {
  type CatalogIndex,
  type FeasibilityReport,
  type Link,
  type Overlay,
  type Palette,
  type ProductView,
  type SceneList,
  type SceneView,
  type SpectrumView,
  type SweepResult,
  type TrayReport,
  type YieldResponse,
  type BibEntry,
  getJson,
  postJson,
  query,
} from './client'

export const LINK_SCENE = 'link' // the procedural worked-example link (brief 03 scene)

export function useDebounced<T>(value: T, ms = 150): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), ms)
    return () => window.clearTimeout(timer)
  }, [value, ms])
  return debounced
}

export function useDisplay(mode: 'light' | 'dark') {
  return useQuery({
    queryKey: ['display', mode],
    queryFn: ({ signal }) => getJson<Palette>(`/display${query({ mode })}`, signal),
    staleTime: Infinity,
  })
}

export function useSceneList() {
  return useQuery({
    queryKey: ['geometry'],
    queryFn: ({ signal }) => getJson<SceneList>('/geometry', signal),
    staleTime: Infinity,
  })
}

export function useScene(scene: string) {
  return useQuery({
    queryKey: ['scene', scene],
    queryFn: ({ signal }) => getJson<SceneView>(`/geometry/${encodeURIComponent(scene)}`, signal),
    enabled: scene !== LINK_SCENE,
    staleTime: Infinity,
  })
}

export function useOverlay(
  scene: string,
  mode: 'light' | 'dark',
  overlayCase: string | null,
  isolationDb: number | null,
) {
  return useQuery({
    queryKey: ['overlay', scene, mode, overlayCase, isolationDb],
    queryFn: ({ signal }) =>
      getJson<Overlay>(
        `/overlay/${encodeURIComponent(scene)}${query({ mode, case: overlayCase, isolation_db: isolationDb })}`,
        signal,
      ),
    enabled: scene !== LINK_SCENE,
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    retry: false,
  })
}

export function useCatalog() {
  return useQuery({
    queryKey: ['catalog'],
    queryFn: ({ signal }) => getJson<CatalogIndex>('/catalog', signal),
    staleTime: Infinity,
  })
}

export function useProduct(product: string, hypotheses: readonly string[], overrides: Record<string, number>) {
  const plain = hypotheses.length === 0 && Object.keys(overrides).length === 0
  return useQuery({
    queryKey: ['product', product, hypotheses, overrides],
    queryFn: ({ signal }) =>
      plain
        ? getJson<ProductView>(`/catalog/${encodeURIComponent(product)}`, signal)
        : postJson<ProductView>(
            `/inference/${encodeURIComponent(product)}`,
            { hypotheses, overrides },
            signal,
          ),
    enabled: product !== '',
    placeholderData: keepPreviousData,
    staleTime: Infinity,
  })
}

export function useReferences() {
  return useQuery({
    queryKey: ['references'],
    queryFn: ({ signal }) => getJson<{ entries: BibEntry[] }>('/references', signal),
    staleTime: Infinity,
    select: (data) => new Map(data.entries.map((e) => [e.key, e])),
  })
}

export function useProfile(name: string) {
  return useQuery({
    queryKey: ['profile', name],
    queryFn: ({ signal }) => getJson<Link>(`/profiles/${encodeURIComponent(name)}`, signal),
    staleTime: Infinity,
  })
}

export function useEvaluate(link: Link | null) {
  const debounced = useDebounced(link)
  return useQuery({
    queryKey: ['evaluate', debounced],
    queryFn: ({ signal }) => postJson<FeasibilityReport>('/evaluate', debounced, signal),
    enabled: debounced !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export interface SweepAxis {
  path: string
  start: number
  stop: number
  num: number
}

export function useSweep(link: Link | null, x: SweepAxis, y: SweepAxis, enabled: boolean) {
  const debounced = useDebounced(link, 250)
  return useQuery({
    queryKey: ['sweep', debounced, x, y],
    queryFn: ({ signal }) => postJson<SweepResult>('/sweep', { link: debounced, x, y }, signal),
    enabled: enabled && debounced !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useTray(lanes: Link[] | null, enabled: boolean) {
  const debounced = useDebounced(lanes, 200)
  return useQuery({
    queryKey: ['tray', debounced],
    queryFn: ({ signal }) => postJson<TrayReport>('/evaluate_tray', { name: 'tray', lanes: debounced }, signal),
    enabled: enabled && debounced !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useYield(link: Link | null, enabled: boolean) {
  const debounced = useDebounced(link, 250)
  return useQuery({
    queryKey: ['yield', debounced],
    queryFn: ({ signal }) =>
      postJson<YieldResponse>('/yield', { link: debounced, n_samples: 100000, seed: 0, bins: 60 }, signal),
    enabled: enabled && debounced !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

export function useSpectrum(hypothesis: string, enabled: boolean) {
  return useQuery({
    queryKey: ['spectrum', hypothesis],
    queryFn: ({ signal }) => getJson<SpectrumView>(`/spectrum/bidi16${query({ hypothesis })}`, signal),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: Infinity,
  })
}
