import { expect, test } from '@playwright/test'

test.use({ baseURL: process.env.STAGING_URL, ignoreHTTPSErrors: true })

test('production build supports HTTPS login, deep links, restoration and logout', async ({ page }) => {
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.addInitScript(() => {
    window.stagingCspViolations = []
    document.addEventListener('securitypolicyviolation', event => {
      window.stagingCspViolations.push(event.violatedDirective)
    })
  })
  await page.goto('/requests')
  await expect(page.getByRole('heading', { name: 'Welcome back', exact: true })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(process.env.STAGING_PROBE_EMAIL)
  await page.getByLabel('Password', { exact: true }).fill(process.env.STAGING_PROBE_PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible()
  await page.goto('/suppliers')
  await expect(page.getByRole('heading', { name: 'Supplier directory', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Supplier directory', exact: true })).toBeVisible()
  expect(await page.evaluate(() => window.stagingCspViolations)).toEqual([])
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back', exact: true })).toBeVisible()
  expect(errors).toEqual([])
})
