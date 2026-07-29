import { test, expect } from '@playwright/test'

const run = Date.now()

test('no console errors or warnings during a full project + share flow', async ({ page }) => {
  const messages = []
  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      messages.push(`[${msg.type()}] ${msg.text()}`)
    }
  })
  page.on('pageerror', (err) => {
    messages.push(`[pageerror] ${err.message}`)
  })

  const email = `console-check-${run}@example.com`
  const projectName = `Console Check Project ${run}`

  await page.goto('/register')
  await page.getByPlaceholder('Jane Doe').fill('Console Check')
  await page.locator('input[type="email"]').fill(email)
  await page.locator('input[type="password"]').fill('secret123')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/dashboard/)

  await page.goto('/projects/new')
  await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
  await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()

  // Every new project requires a schedule before it's usable - fill the
  // blocking dialog (Start Date is pre-filled with today) before the
  // "was created" confirmation becomes reachable.
  await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible()
  const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  await page.locator('input[type="date"]').last().fill(deadline)
  await page.getByRole('button', { name: 'Save Schedule' }).click()

  await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()
  await page.getByRole('link', { name: 'Go to Project' }).click()
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

  await page.getByRole('button', { name: 'Share' }).click()
  const modal = page.getByRole('dialog', { name: 'Share Project' })
  await expect(modal.getByRole('button', { name: /Copy Link/ })).toBeVisible()
  await modal.getByRole('button', { name: /Copy Link/ }).click()
  await page.keyboard.press('Escape')

  await page.getByRole('link', { name: 'Back to Projects' }).click()
  await expect(page).toHaveURL(/\/projects$/)

  const card = page.locator('[data-testid="project-card"]', { hasText: projectName })
  await card.getByRole('button', { name: 'Project actions' }).click()
  await page.getByRole('menuitem', { name: 'Delete' }).click()
  await page.getByRole('button', { name: 'Delete project' }).click()
  await expect(page.getByText('Project deleted')).toBeVisible()

  expect(messages, `Unexpected console errors/warnings:\n${messages.join('\n')}`).toEqual([])
})
