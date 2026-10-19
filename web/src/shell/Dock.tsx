// Bottom dock: analysis tabs. Chart views are code-split and load on first use.

import * as Tabs from '@radix-ui/react-tabs'
import { Suspense, lazy } from 'react'
import type { FeasibilityReport, SceneView } from '../api/client'
import { LINK_SCENE, useCatalog, useProduct } from '../api/hooks'
import { useExplorer } from '../state/store'
import { DOCK_TABS, type DockTab } from '../state/url'
import { Empty } from './ui'

const LinkBudget = lazy(() => import('../views/LinkBudget'))
const Spectrum = lazy(() => import('../views/Spectrum'))
const DesignSpace = lazy(() => import('../views/DesignSpace'))
const TrayView = lazy(() => import('../views/TrayView'))
const Upstream = lazy(() => import('../views/Upstream'))
const YieldView = lazy(() => import('../views/YieldView'))
const Inference = lazy(() => import('../views/Inference'))
const SpecSheet = lazy(() => import('../views/SpecSheet'))
const Physics = lazy(() => import('../views/Physics'))

export const TAB_LABELS: Record<DockTab, string> = {
  budget: 'Link budget',
  spectrum: 'Spectrum',
  design: 'Design space',
  tray: 'Tray',
  upstream: 'Upstream',
  yield: 'Yield',
  inference: 'Inference',
  spec: 'Spec sheet',
  physics: 'Physics',
}

export function Dock({ view, report, pending }: { view: SceneView | undefined; report: FeasibilityReport | undefined; pending: boolean }) {
  const tab = useExplorer((s) => s.dockTab)
  const setTab = useExplorer((s) => s.setDockTab)
  const scene = useExplorer((s) => s.scene)
  const hypotheses = useExplorer((s) => s.hypotheses)
  const product = scene === LINK_SCENE ? '' : (view?.scene.scene.product ?? '')
  const productTabs = tab === 'inference' || tab === 'spec' || tab === 'physics'
  // only this product's hypotheses go to POST /inference
  const summary = useCatalog().data?.products.find((p) => p.id === product)
  const own = hypotheses.filter((h) => summary?.hypotheses.some((x) => x.id === h))
  const productView = useProduct(productTabs ? product : '', own, {})
  return (
    <Tabs.Root value={tab} onValueChange={(v) => setTab(v as DockTab)} className="dock">
      <Tabs.List className="dock-tabs" aria-label="Analyses">
        {DOCK_TABS.map((t) => (
          <Tabs.Trigger key={t} value={t} className="dock-tab" data-testid={`tab-${t}`}>
            {TAB_LABELS[t]}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      <Suspense fallback={<Empty>Loading the view…</Empty>}>
        <Tabs.Content value="budget" className="dock-panel">
          <LinkBudget report={report} pending={pending} />
        </Tabs.Content>
        <Tabs.Content value="spectrum" className="dock-panel">
          {tab === 'spectrum' && <Spectrum />}
        </Tabs.Content>
        <Tabs.Content value="design" className="dock-panel">
          {tab === 'design' && <DesignSpace />}
        </Tabs.Content>
        <Tabs.Content value="tray" className="dock-panel">
          {tab === 'tray' && <TrayView />}
        </Tabs.Content>
        <Tabs.Content value="upstream" className="dock-panel">
          {tab === 'upstream' && <Upstream report={report} />}
        </Tabs.Content>
        <Tabs.Content value="yield" className="dock-panel">
          {tab === 'yield' && <YieldView />}
        </Tabs.Content>
        <Tabs.Content value="inference" className="dock-panel">
          {tab === 'inference' && (productView.isError ? <Empty>{String(productView.error)}</Empty> : <Inference product={productView.data} />)}
        </Tabs.Content>
        <Tabs.Content value="spec" className="dock-panel">
          {tab === 'spec' && <SpecSheet product={productView.data} />}
        </Tabs.Content>
        <Tabs.Content value="physics" className="dock-panel">
          {tab === 'physics' && <Physics product={productView.data} />}
        </Tabs.Content>
      </Suspense>
    </Tabs.Root>
  )
}
