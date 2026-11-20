import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: process.env.STAGING_URL ? 'staging.spec.js' : 'procurement.spec.js',
  workers: 1,
  retries: 0,
  timeout: 90000,
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:5173',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
})
