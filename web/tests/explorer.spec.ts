import { type Page, expect, test } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const img = (name: string) => fileURLToPath(new URL(`../../docs/img/${name}.png`, import.meta.url))

async function open(page: Page, query: string) {
  await page.goto(`/?still=1&${query}`)
  await settle(page)
}

async function settle(page: Page) {
  await page.waitForTimeout(250)
  await expect(page.locator('.viewport')).toHaveAttribute('data-settled', 'true', { timeout: 120_000 })
}

const SCENES: [string, string][] = [
  ['reference_rack', 'Rack'],
  ['switch_tray', 'Rack › Switch tray'],
  ['xpu_tray', 'Rack › XPU tray'],
  ['bidi_engine', 'Rack › Switch tray › Engine'],
  ['bidi_link', 'Rack › Switch tray › Engine › BiDi link'],
  ['photonic_interposer', 'interposer'],
  ['cpo_chiplet', '32T chiplet'],
  ['laser_sources', 'Rack › Switch tray › ELS-DR'],
  ['pic_region', 'Rack › Switch tray › Engine › PIC'],
  ['ring_section', 'Rack › Switch tray › Engine › PIC › Ring'],
  ['photonic_processor', 'Processor'],
]

test('every scene renders from the API with its breadcrumb, spec sheet and independence line', async ({ page }) => {
  test.setTimeout(900_000)
  for (const [scene, crumbs] of SCENES) {
    await open(page, `scene=${scene}&tab=spec`)
    await expect(page.getByTestId('breadcrumb')).toHaveText(crumbs.replaceAll(' › ', ''))
    await expect(page.getByTestId('spec-sheet')).toBeVisible()
    await expect(page.getByTestId('independence')).toHaveText(
      'Independent model built from public information. Not affiliated with or endorsed by any company whose publications are cited.',
    )
    await page.screenshot({ path: img(`scene_${scene}`) })
  }
})

test('BiDi engine: exploded view, then section view with caps', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=bidi_engine&tab=physics')
  await page.keyboard.press('e')
  await expect(page.getByRole('slider', { name: 'Explode' })).toHaveAttribute('aria-valuenow', '1', { timeout: 10_000 })
  await settle(page)
  await page.screenshot({ path: img('engine_exploded') })
  await page.keyboard.press('e')
  await expect(page.getByRole('slider', { name: 'Explode' })).toHaveAttribute('aria-valuenow', '0', { timeout: 10_000 })
  await page.keyboard.press('s')
  await expect(page.getByRole('slider', { name: 'Section position' })).toBeVisible()
  await expect(page).toHaveURL(/section=x/)
  await page.keyboard.press('1')
  await settle(page)
  await page.screenshot({ path: img('section') })
})

test('measure the BiDi engine outline: 37.5 mm, the OFC 2026 length', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=bidi_engine&tab=physics')
  await page.keyboard.press('m')
  const corner = (signs: number[]) =>
    page.evaluate((s) => (window as unknown as { __oicd: { corner: (p: string, s: number[]) => { x: number; y: number } } }).__oicd.corner('eng.outline', s), signs)
  const a = await corner([-1, -1, 1])
  const b = await corner([1, -1, 1])
  await page.mouse.click(a.x + 4, a.y + 2)
  await page.mouse.click(b.x - 4, b.y + 2)
  await expect(page.getByTestId('measure-value')).toHaveText('37.5 mm')
})

test('semantic zoom from the rack down to the ring cross-section', async ({ page }) => {
  test.setTimeout(600_000)
  await open(page, 'scene=reference_rack&tab=spec')
  const zoomInto = async (part: RegExp, scene: string) => {
    await page.getByRole('button', { name: part }).first().click()
    await page.keyboard.press('Enter')
    await expect(page.locator('.viewport')).toHaveAttribute('data-scene', scene, { timeout: 120_000 })
    await settle(page)
  }
  await zoomInto(/^CPO switch trays/, 'switch_tray')
  await zoomInto(/^BiDi engines/, 'bidi_engine')
  await zoomInto(/^photonic IC \(PIC\)/, 'pic_region')
  await zoomInto(/^ring modulator \(MRM\)/, 'ring_section')
  await expect(page.getByTestId('breadcrumb')).toHaveText('RackSwitch trayEnginePICRing')
  await expect(page.locator('.vp-sub')).toContainText('nm')
  await page.screenshot({ path: img('semantic_zoom_ring') })
  // and back up one level
  await page.keyboard.press('Backspace')
  await expect(page.locator('.viewport')).toHaveAttribute('data-scene', 'pic_region', { timeout: 120_000 })
})

test('command palette reaches products and analyses', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=reference_rack')
  await page.keyboard.press('ControlOrMeta+k')
  await page.keyboard.type('external laser sources')
  await page.keyboard.press('Enter')
  await expect(page.locator('.viewport')).toHaveAttribute('data-scene', 'laser_sources', { timeout: 120_000 })
  await page.keyboard.press('ControlOrMeta+k')
  await page.keyboard.type('analysis spectrum')
  await page.keyboard.press('Enter')
  await expect(page.getByTestId('tab-spectrum')).toHaveAttribute('data-state', 'active')
})

test('rack reference plane: the FAU in the module flips EXCLUDED to NOT_EXCLUDED', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=reference_rack&tab=physics')
  await expect(page.getByTestId('overlay-verdict')).toHaveAttribute('data-status', 'EXCLUDED')
  await expect(page.getByTestId('overlay-margin')).toHaveText('−1.0016')
  await page.getByTestId('case-H_fau_module').click()
  await expect(page.getByTestId('overlay-verdict')).toHaveAttribute('data-status', 'NOT_EXCLUDED')
  await expect(page.getByTestId('overlay-margin')).toHaveText('+1.9984')
  await settle(page)
  await page.screenshot({ path: img('rack_reference_plane') })
})

test('design space: the sweep around the worked example', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=link&tab=design')
  await expect(page.getByTestId('design-space')).toContainText('design margin 0.4992 dB')
  await page.waitForTimeout(800)
  await page.screenshot({ path: img('sweep') })
})

test('tray: lane 5 at 2.0 dB decides the tray at −0.5008 dB', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=link&tab=tray')
  await page.getByRole('button', { name: '5', exact: true }).click()
  await page.getByLabel('lane 5 patch connector loss (dB)', { exact: true }).fill('2')
  await expect(page.getByTestId('tray-margin')).toHaveText('-0.5008')
  await expect(page.getByTestId('tray-deciding')).toHaveText('5')
  await expect(page.getByTestId('tray-verdict')).toHaveAttribute('data-status', 'EXCLUDED')
  await page.waitForTimeout(600)
  await page.screenshot({ path: img('tray') })
})

test('upstream: N = 17 is the maximum fan-out, N = 18 is EXCLUDED', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=link&tab=upstream')
  await page.getByTestId('load-upstream').click()
  await expect(page.getByTestId('max-fanout')).toHaveText('17')
  await page.getByLabel('fan-out N').fill('17')
  await expect(page.getByTestId('upstream-verdict')).toHaveAttribute('data-status', 'NOT_EXCLUDED')
  await expect(page.getByTestId('upstream-margin')).toHaveText('0.0448')
  await page.getByLabel('fan-out N').fill('18')
  await expect(page.getByTestId('upstream-verdict')).toHaveAttribute('data-status', 'EXCLUDED')
  await expect(page.getByTestId('upstream-margin')).toHaveText('-0.2034')
  await settle(page)
  await page.screenshot({ path: img('upstream') })
})

test('yield: the model card §11 case', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=link&tab=yield')
  await page.getByTestId('load-yield').click()
  await expect(page.getByTestId('yield-analytic')).toHaveText('92.522 %')
  await page.waitForTimeout(800)
  await page.screenshot({ path: img('yield') })
})

test('spectrum: the worst receive channel moves with the ring FSR hypothesis', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=bidi_link&tab=spectrum')
  await expect(page.getByTestId('spectrum-worst')).toContainText('3:')
  await page.getByRole('radio', { name: 'H_fsr32' }).click()
  await expect(page.getByTestId('spectrum-worst')).toContainText('7:')
  await page.waitForTimeout(800)
  await page.screenshot({ path: img('spectrum') })
})

test('inference: graph, hypotheses and support matrix for the switch tray', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=switch_tray&tab=inference')
  await expect(page.getByTestId('inference-graph')).toBeVisible({ timeout: 60_000 })
  await expect(page.getByTestId('support-matrix')).toBeVisible()
  await page.getByTestId('hyp-H_dir').check()
  await expect(page).toHaveURL(/hyp=H_dir/)
  await page.waitForTimeout(800)
  await page.screenshot({ path: img('inference') })
})

test('photonic processor: the ABFP simulator answers from the API', async ({ page }) => {
  test.setTimeout(300_000)
  await open(page, 'scene=photonic_processor&tab=physics')
  const simulator = page.getByTestId('ptc-simulator')
  await expect(simulator).toBeVisible()
  // model card §15.4: the error falls as G rises from 1 to the design target of 4
  const errorAt = async (gain: string) => {
    await page.getByLabel('gain G ()', { exact: true }).fill(gain)
    await expect(page.getByTestId('ptc-simulator')).toContainText(`gain G`)
    await page.waitForTimeout(800)
    return Number((await page.getByTestId('ptc-error').textContent())?.replace(' %', ''))
  }
  const atOne = await errorAt('1')
  const atFour = await errorAt('4')
  expect(atFour).toBeLessThan(atOne)
  await page.getByTestId('tab-physics').click() // leave the number box, so E reaches the viewport
  await page.keyboard.press('e')
  await expect(page.getByRole('slider', { name: 'Explode' })).toHaveAttribute('aria-valuenow', '1', { timeout: 10_000 })
  await settle(page)
  await page.screenshot({ path: img('processor_exploded') })
})
