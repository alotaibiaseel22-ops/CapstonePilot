import { test, expect } from '@playwright/test'

const run = Date.now()

async function fillProjectSchedule(page) {
  await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible({
    timeout: 45_000,
  })
  const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  await page.locator('input[type="date"]').last().fill(deadline)
  await page.getByRole('button', { name: 'Save Schedule' }).click()
}

test.describe('Task assignment (members and guests)', () => {
  test('a task can be assigned to a member, then a guest, then unassigned', async ({ browser }) => {
    test.setTimeout(90_000)
    const ownerEmail = `assign-owner-${run}@example.com`
    const collabEmail = `assign-collab-${run}@example.com`
    const projectName = `Assignment Test Project ${run}`

    const context = await browser.newContext()
    const page = await context.newPage()

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Assign Owner')
    await page.locator('input[type="email"]').fill(ownerEmail)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'proposal.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Build a small internal tool for tracking office supplies.'),
    })
    await expect(page.getByText('Selected: proposal.txt')).toBeVisible()
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible({ timeout: 45_000 })
    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    // Invite a collaborator by email and have them onboard with just a name.
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await page.getByPlaceholder('name@example.com').fill(collabEmail)
    await page.getByRole('button', { name: 'Invite', exact: true }).click()
    await expect(page.getByText(`Invitation sent to ${collabEmail}`)).toBeVisible()
    const row = modal.locator('[data-testid="pending-invitation-row"]').filter({ hasText: collabEmail })
    await row.getByLabel(`Actions for ${collabEmail}`).click()
    await page.getByRole('menuitem', { name: 'Copy Invite Link' }).click()
    const collabInviteLink = await page.evaluate(() => navigator.clipboard.readText())
    // Only the row's own dropdown menu closes here (DropdownMenu.jsx closes
    // itself on item click) - the Share modal underneath stays open, still
    // needed below for the shareable-link "Copy Link" button.
    await expect(modal).toBeVisible()

    const collabContext = await browser.newContext()
    const collabPage = await collabContext.newPage()
    await collabPage.goto(collabInviteLink)
    await expect(collabPage.getByRole('heading', { name: `Join ${projectName}` })).toBeVisible()
    await collabPage.getByPlaceholder('Jane Doe').fill('Assign Collaborator')
    await collabPage.getByRole('button', { name: 'Join Project' }).click()
    await expect(collabPage).toHaveURL(/\/projects\/[0-9a-f-]+$/)
    await collabContext.close()

    // Get a shareable link and join as a guest.
    await modal.getByRole('button', { name: /Copy Link/ }).click()
    const shareableLink = await page.evaluate(() => navigator.clipboard.readText())
    await page.keyboard.press('Escape')

    const guestContext = await browser.newContext()
    const guestPage = await guestContext.newPage()
    await guestPage.goto(shareableLink)
    await expect(guestPage).toHaveURL(/\/guest\//)
    await guestPage.getByPlaceholder('Jane Doe').fill('Assign Guest')
    await guestPage.getByRole('button', { name: 'Continue' }).click()
    await expect(guestPage.getByText(projectName)).toBeVisible()

    // Back on the owner's side: open the plan, expand the first milestone,
    // and assign its first task. Reload first - the Share modal opened
    // earlier already cached the (then-collaborator-less) members list for
    // 30s (queryClient.js's default staleTime), so without a reload here
    // this would race that stale cache instead of proving real behavior.
    await page.getByRole('link', { name: 'View Plan' }).click()
    await expect(page).toHaveURL(/\/progress$/)
    await page.reload()
    await page.getByTestId('milestone-accordion-toggle').first().click()

    const assignButton = page.getByLabel(/^Assign /).first()
    await expect(assignButton).toBeVisible({ timeout: 10_000 })
    await assignButton.click()
    await page.getByRole('menuitem', { name: /Assign Collaborator/ }).click()
    await expect(page.getByLabel(/^Reassign /).first()).toBeVisible()

    // Reassign the same task to the guest instead.
    await page.getByLabel(/^Reassign /).first().click()
    await page.getByRole('menuitem', { name: /Assign Guest.*Guest/ }).click()

    // The guest should now see the task and be able to advance its status.
    await guestPage.reload()
    const guestTaskToggle = guestPage.getByLabel(/^Advance status for /).first()
    await expect(guestTaskToggle).toBeEnabled({ timeout: 10_000 })
    await guestTaskToggle.click()

    // Owner unassigns the task.
    await page.getByLabel(/^Reassign /).first().click()
    await page.getByRole('menuitem', { name: 'Unassign' }).click()
    await expect(page.getByLabel(/^Assign /).first()).toBeVisible()

    // The guest can no longer act on it.
    await guestPage.reload()
    await expect(guestPage.getByLabel(/not assigned to you/).first()).toBeDisabled()

    await guestContext.close()
    await context.close()
  })
})
