import { test, expect } from '@playwright/test'

const run = Date.now()

test.describe('Share never navigates away from the project', () => {
  test('the post-creation "Invite Team Members" button opens the modal, not Settings', async ({ page }) => {
    const email = `share-nav-${run}@example.com`
    const projectName = `Share Nav Check ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Share Nav')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()

    const urlBeforeClick = page.url()
    await page.getByRole('button', { name: 'Invite Team Members' }).click()

    // The URL must not change at all - not to /settings, not anywhere.
    await expect(page).toHaveURL(urlBeforeClick)
    expect(page.url()).not.toContain('/settings')

    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await expect(modal).toBeVisible()
    await expect(modal.getByRole('button', { name: /Copy Link/ })).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(modal).toHaveCount(0)
    await expect(page).toHaveURL(urlBeforeClick)
  })

  test('the Share button on Project Detail never navigates to Settings', async ({ page }) => {
    const email = `share-nav2-${run}@example.com`
    const projectName = `Share Nav Check 2 ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Share Nav Two')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()
    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    const projectUrl = page.url()
    await page.getByRole('button', { name: 'Share', exact: true }).click()

    await expect(page).toHaveURL(projectUrl)
    expect(page.url()).not.toContain('/settings')
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await expect(modal).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(modal).toHaveCount(0)
    await expect(page).toHaveURL(projectUrl)
  })
})
