import { expect, test } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const SCREENSHOT = fileURLToPath(new URL('../../docs/img/explorer.png', import.meta.url))

test('worked example, then +1 dB on the patch connector flips the verdict', async ({ page }) => {
  await page.goto('/')

  // Model card §4: M_net = +0.4992 dB, not excluded.
  await expect(page.getByTestId('verdict')).toHaveText('NOT_EXCLUDED')
  await expect(page.getByTestId('margin')).toHaveText('0.4992')

  const patch = page.getByLabel('patch connector loss (dB)', { exact: true })
  await expect(patch).toHaveValue('1')
  await patch.fill('2')

  // 1.0 -> 2.0 dB: M_net = 0.4992 - 1 = -0.5008 dB, excluded (computed by the engine).
  await expect(page.getByTestId('verdict')).toHaveText('EXCLUDED')
  await expect(page.getByTestId('margin')).toHaveText('-0.5008')
  await expect(page.locator('.badge-verdict')).toHaveText('EXCLUDED')

  await page.waitForTimeout(800) // let the camera and chart settle before the screenshot
  await page.screenshot({ path: SCREENSHOT })
})
