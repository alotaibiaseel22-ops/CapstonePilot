import { test, expect } from '@playwright/test'

const run = Date.now()

test.describe('Collaborators list (owner + members + guests)', () => {
  test('owner + 3 guests shows a count of 4 with no duplicates and no missing entries', async ({
    browser,
  }) => {
    test.setTimeout(60_000)
    const ownerEmail = `collab-owner-${run}@example.com`
    const projectName = `Collab Roster Test ${run}`

    function collaboratorsCount() {
      return page.getByText('Collaborators', { exact: true }).locator('..').locator('p.text-3xl')
    }

    const context = await browser.newContext()
    const page = await context.newPage()

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Aseel')
    await page.locator('input[type="email"]').fill(ownerEmail)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page
      .getByPlaceholder('What is this project about?')
      .fill('A project created by an automated Playwright test.')
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible()
    const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    await page.locator('input[type="date"]').last().fill(deadline)
    await page.getByRole('button', { name: 'Save Schedule' }).click()
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()
    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    // Before any guest joins: Collaborators = 1 (owner only).
    await expect(collaboratorsCount()).toHaveText('1')

    // Get the shareable link, then join 3 distinct guests via 3 separate
    // browser contexts (matching real independent-device usage).
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await modal.getByRole('button', { name: /Copy Link/ }).click()
    const shareableLink = await page.evaluate(() => navigator.clipboard.readText())
    await page.keyboard.press('Escape')

    for (const guestName of ['Haneen', 'Sara', 'Mohammed']) {
      const guestContext = await browser.newContext()
      const guestPage = await guestContext.newPage()
      await guestPage.goto(shareableLink)
      await expect(guestPage).toHaveURL(/\/guest\//)
      await guestPage.getByPlaceholder('Jane Doe').fill(guestName)
      await guestPage.getByRole('button', { name: 'Continue' }).click()
      await expect(guestPage.getByText(projectName)).toBeVisible()
      await guestContext.close()
    }

    // Owner reloads: Collaborators card must read 4 (owner + 3 guests).
    await page.reload()
    await expect(collaboratorsCount()).toHaveText('4', { timeout: 10_000 })

    // The Share modal's list (the "dropdown") must show all 4, correctly
    // labeled, no duplicates, no missing entries.
    await page.getByRole('button', { name: 'Share' }).click()
    const modal2 = page.getByRole('dialog', { name: 'Share Project' })
    await expect(modal2.getByText('Aseel', { exact: false }).first()).toBeVisible()
    for (const guestName of ['Haneen', 'Sara', 'Mohammed']) {
      await expect(modal2.getByText(guestName)).toHaveCount(1)
    }
    await expect(modal2.getByText('Aseel')).toHaveCount(1)
    await expect(modal2.locator('[data-testid="access-row"]')).toHaveCount(4)

    await context.close()
  })
})
