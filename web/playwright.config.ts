import { defineConfig, devices } from '@playwright/test'

// Starts the engine API (port 8000) and the Vite dev server (port 5173) unless already running.
export default defineConfig({
  testDir: './tests',
  // CI runners render WebGL in software (SwiftShader) and run about twice as slow as a laptop.
  timeout: process.env.CI ? 180_000 : 60_000,
  expect: { timeout: process.env.CI ? 30_000 : 15_000 },
  // The github reporter turns failures into check-run annotations, readable without the log.
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: 'http://localhost:5173',
    ...devices['Desktop Chrome'],
    viewport: { width: 1440, height: 1000 },
    // Linux runners have no GPU: render WebGL in software there.
    launchOptions: { args: process.platform === 'linux' ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [] },
  },
  webServer: [
    {
      command: 'uv run uvicorn oicd.api:app --port 8000',
      cwd: '..',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
})
