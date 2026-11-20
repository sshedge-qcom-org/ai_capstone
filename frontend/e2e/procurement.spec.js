import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { expect, test } from '@playwright/test'

const require = createRequire(import.meta.url)
const axeSource = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8')
const password = process.env.DEMO_PASSWORD

async function login(page, role) {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(`${role}@company.com`)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible()
}

async function logout(page) {
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back', exact: true })).toBeVisible()
}

async function checkAccessibility(page) {
  await page.addScriptTag({ content: axeSource })
  const violations = await page.evaluate(async () => {
    const result = await window.axe.run({
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] },
    })
    return result.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(node => node.target) }))
  })
  expect(violations).toEqual([])
}

test('employee registration and protected-route role guard', async ({ page }) => {
  if (!password) throw new Error('DEMO_PASSWORD must be set for local seeded browser verification')
  await page.goto('/requests')
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await page.getByRole('link', { name: 'Create an account' }).click()
  await page.getByLabel('Full name').fill('Browser Verification Employee')
  await page.getByLabel('Email', { exact: true }).fill(`browser-${Date.now()}@example.com`)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Create account', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible()
  await page.goto('/admin')
  await expect(page.getByRole('heading', { name: 'Access restricted' })).toBeVisible()
})

test('complete request-to-delivery journey, reports and responsive accessibility', async ({ page }) => {
  if (!password) throw new Error('DEMO_PASSWORD must be set for local seeded browser verification')
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await login(page, 'employee')
  await page.getByRole('link', { name: '+ New request' }).click()
  const title = `Browser verified laptop ${Date.now()}`
  await page.getByLabel('Item name').fill(title)
  await page.getByRole('combobox', { name: 'Category', exact: true }).selectOption('IT Equipment')
  await page.getByLabel('Quantity', { exact: true }).fill('2')
  await page.getByLabel('Estimated total budget (USD)').fill('2400.50')
  await page.getByLabel('Target delivery date').fill(new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10))
  await page.getByLabel('Justification').fill('Two laptops for the new engineering onboarding cohort.')
  await page.getByRole('button', { name: 'Submit for approval', exact: true }).click()
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
  const requestUrl = page.url()
  await page.getByLabel('New comment').fill('Please include the standard warranty.')
  await page.getByRole('button', { name: 'Post comment', exact: true }).click()
  await expect(page.getByText('Please include the standard warranty.', { exact: true })).toBeVisible()
  await logout(page)
  await login(page, 'manager')
  await page.goto(requestUrl)
  await page.getByRole('button', { name: 'Reply', exact: true }).click()
  await page.getByLabel('Your reply').fill('Confirmed. The standard warranty is included.')
  await page.getByRole('button', { name: 'Post reply', exact: true }).click()
  await expect(page.getByRole('button', { name: /Show replies \(1\)/ })).toBeVisible()
  await page.getByRole('button', { name: /Show replies \(1\)/ }).click()
  await expect(page.getByText('Confirmed. The standard warranty is included.', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Approve', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Recommended suppliers' })).toBeVisible()
  page.once('dialog', dialog => dialog.accept())
  const created = page.waitForResponse(response => response.url().endsWith('/api/v1/orders') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Select & create order' }).first().click()
  const orderResponse = await created
  expect(orderResponse.status()).toBe(201)
  const order = await orderResponse.json()
  await expect(page.getByRole('heading', { name: `PO-${String(order.id).padStart(5, '0')}` })).toBeVisible()
  const orderUrl = page.url()
  await logout(page)
  await login(page, 'admin')
  await page.getByRole('link', { name: 'Administration', exact: true }).click()
  const vendorForm = page.locator('form').filter({ hasText: 'vendor@company.com' })
  await vendorForm.getByLabel('Supplier ID').fill(String(order.supplier_id))
  const saved = page.waitForResponse(response => /\/api\/v1\/users\/\d+$/.test(response.url()) && response.request().method() === 'PATCH')
  await vendorForm.getByRole('button', { name: 'Save access' }).click()
  expect((await saved).status()).toBe(200)
  await page.getByRole('link', { name: 'Reports', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Reports & analytics' })).toBeVisible()
  await checkAccessibility(page)
  const downloaded = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export CSV', exact: true }).first().click()
  expect((await downloaded).suggestedFilename()).toBe('spending_by_category.csv')
  await logout(page)
  await login(page, 'vendor')
  await page.goto(orderUrl)
  for (const status of ['processing', 'shipped', 'delivered']) {
    page.once('dialog', dialog => dialog.accept())
    const updated = page.waitForResponse(response => response.url().endsWith(`/orders/${order.id}/status`) && response.request().method() === 'PATCH')
    await page.getByRole('button', { name: `Mark as ${status}`, exact: true }).click()
    expect((await updated).status()).toBe(200)
  }
  await expect(page.getByRole('button', { name: /^Mark as/ })).toHaveCount(0)
  await page.setViewportSize({ width: 390, height: 844 })
  await checkAccessibility(page)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.setViewportSize({ width: 320, height: 720 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  expect(errors).toEqual([])
})
