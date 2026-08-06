import { test, expect } from '@playwright/test'

const run = Date.now()

async function fillProjectSchedule(page) {
  await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible()
  const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  await page.locator('input[type="date"]').last().fill(deadline)
  await page.getByRole('button', { name: 'Save Schedule' }).click()
}

test.describe('Attachments and comments (owner and guest)', () => {
  test('owner and guest can both upload files and post comments, and the owner can moderate', async ({
    browser,
  }) => {
    test.setTimeout(60_000)
    const ownerEmail = `attach-owner-${run}@example.com`
    const projectName = `Attachments Test Project ${run}`

    const context = await browser.newContext()
    const page = await context.newPage()

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Attach Owner')
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
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()
    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    // Owner uploads a file and posts a comment.
    await page.getByRole('link', { name: 'Attachments' }).click()
    await expect(page).toHaveURL(/\/attachments$/)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'owner-notes.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Owner uploaded notes.'),
    })
    await expect(page.getByText('owner-notes.txt')).toBeVisible()

    await page.goBack()
    await page.getByRole('link', { name: 'Comments' }).click()
    await expect(page).toHaveURL(/\/comments$/)
    await page.getByPlaceholder('Write a comment...').fill('Hello from the owner')
    await page.getByRole('button', { name: 'Post Comment' }).click()
    await expect(page.getByText('Hello from the owner')).toBeVisible()

    // Get the shareable link and join as a guest in a separate context.
    await page.goBack()
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await modal.getByRole('button', { name: /Copy Link/ }).click()
    const shareableLink = await page.evaluate(() => navigator.clipboard.readText())
    await page.keyboard.press('Escape')

    const guestContext = await browser.newContext()
    const guestPage = await guestContext.newPage()
    await guestPage.goto(shareableLink)
    await expect(guestPage).toHaveURL(/\/guest\//)
    await guestPage.getByPlaceholder('Jane Doe').fill('Attach Guest')
    await guestPage.getByRole('button', { name: 'Continue' }).click()
    await expect(guestPage.getByText(projectName)).toBeVisible()

    // Guest sees the owner's attachment and comment, and adds their own.
    await expect(guestPage.getByText('owner-notes.txt')).toBeVisible()
    await expect(guestPage.getByText('Hello from the owner')).toBeVisible()

    await guestPage.locator('input[type="file"]').setInputFiles({
      name: 'guest-file.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Guest uploaded file.'),
    })
    await expect(guestPage.getByText('guest-file.txt')).toBeVisible()

    await guestPage.getByPlaceholder('Write a comment...').fill('Hello from the guest')
    await guestPage.getByRole('button', { name: 'Post Comment' }).click()
    await expect(guestPage.getByText('Hello from the guest')).toBeVisible()

    // Owner (still on the project detail page after closing Share) opens
    // Comments again and sees the guest's comment, guest-labeled. Reload
    // first - the earlier Comments visit already cached the (then guest-
    // less) list for 30s (queryClient.js's default staleTime).
    await page.getByRole('link', { name: 'Comments' }).click()
    await expect(page).toHaveURL(/\/comments$/)
    await page.reload()
    await expect(page.getByText('Hello from the guest')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('(Guest)').first()).toBeVisible()

    // Owner moderates: deletes the guest's comment. Scoped to the specific
    // CommentRow class combo (not a bare 'div' filter, which would also
    // match ancestor wrappers that don't contain the sibling delete button).
    const guestCommentRow = page.locator('div.flex.gap-3').filter({ hasText: 'Hello from the guest' })
    await guestCommentRow.getByLabel('Delete comment').click()
    await expect(page.getByText('Hello from the guest')).toHaveCount(0)

    // Guest reloads and no longer sees their deleted comment.
    await guestPage.reload()
    await expect(guestPage.getByText('Hello from the guest')).toHaveCount(0)

    await guestContext.close()
    await context.close()
  })
})
