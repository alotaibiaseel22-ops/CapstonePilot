import { test, expect } from '@playwright/test'

const run = Date.now()
const ownerName = 'E2E Owner'
const ownerEmail = `owner-${run}@example.com`
const ownerPassword = 'secret123'
const collaboratorEmail = `collab-${run}@example.com`
const password = 'secret123'
const shareProjectName = `Playwright Share Project ${run}`
const cardDeleteProjectName = `Playwright Card Delete Project ${run}`

let shareableLink = ''

test.describe.serial('CapstonePilot end-to-end', () => {
  let page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })

  test.afterAll(async () => {
    await page.close()
  })

  test('register a new project owner', async () => {
    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill(ownerName)
    await page.locator('input[type="email"]').fill(ownerEmail)
    await page.locator('input[type="password"]').fill(ownerPassword)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('create a project through the 4-step flow', async () => {
    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(shareProjectName)
    await page
      .getByPlaceholder('What is this project about?')
      .fill('A project created by an automated Playwright test.')
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await expect(page.getByText(`"${shareProjectName}" was created`)).toBeVisible()

    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)
    await expect(page.getByRole('heading', { name: shareProjectName })).toBeVisible()
  })

  test('shows breadcrumb and a back-to-projects link on project detail', async () => {
    await expect(page.getByRole('link', { name: 'Back to Projects' })).toBeVisible()
    await expect(page.locator('nav').getByText(shareProjectName)).toBeVisible()
  })

  test('sends an email invitation from the Share dialog', async () => {
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })

    await page.getByPlaceholder('name@example.com').fill(collaboratorEmail)
    await page.getByRole('button', { name: 'Invite', exact: true }).click()

    await expect(page.getByText(`Invitation sent to ${collaboratorEmail}`)).toBeVisible()
    await expect(modal.getByText(collaboratorEmail).first()).toBeVisible()
    await expect(modal.getByText('Pending').first()).toBeVisible()
  })

  test('generates and copies the shareable invite link', async () => {
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await modal.getByRole('button', { name: /Copy Link/ }).click()
    await expect(modal.getByRole('button', { name: 'Copied' })).toBeVisible()

    shareableLink = await page.evaluate(() => navigator.clipboard.readText())
    expect(shareableLink).toContain('/invite/')
  })

  test('regenerates the invite link and invalidates the old one', async () => {
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await modal.getByLabel('Invite link options').click()
    await page.getByRole('menuitem', { name: 'Regenerate Link' }).click()
    await expect(page.getByText('Invite link regenerated')).toBeVisible()

    await modal.getByRole('button', { name: /Copy Link/ }).click()
    const regeneratedLink = await page.evaluate(() => navigator.clipboard.readText())
    expect(regeneratedLink).toContain('/invite/')
    expect(regeneratedLink).not.toBe(shareableLink)
    shareableLink = regeneratedLink
  })

  test('disabling the link removes it and a new one can be created', async () => {
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await modal.getByLabel('Invite link options').click()
    await page.getByRole('menuitem', { name: 'Disable Link' }).click()
    await expect(page.getByText('Invite link disabled')).toBeVisible()
    await expect(modal.getByText('Link sharing is currently disabled for this project.')).toBeVisible()

    await modal.getByRole('button', { name: 'Create New Link' }).click()
    await expect(modal.getByRole('button', { name: /Copy Link/ })).toBeVisible()
    await modal.getByRole('button', { name: /Copy Link/ }).click()

    const newLink = await page.evaluate(() => navigator.clipboard.readText())
    expect(newLink).toContain('/invite/')
    expect(newLink).not.toBe(shareableLink)
    shareableLink = newLink
  })

  test('resends the pending email invitation', async () => {
    const row = page.locator('[data-testid="pending-invitation-row"]').filter({ hasText: collaboratorEmail })
    await row.getByLabel(`Actions for ${collaboratorEmail}`).click()
    await page.getByRole('menuitem', { name: 'Resend Invitation' }).click()
    await expect(page.getByText(`Invitation resent to ${collaboratorEmail}`)).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog', { name: 'Share Project' })).toHaveCount(0)
  })

  test('a new collaborator joins via the shareable link', async ({ browser }) => {
    expect(shareableLink).toContain('/invite/')
    const collabContext = await browser.newContext()
    const collabPage = await collabContext.newPage()

    await collabPage.goto(shareableLink)
    await expect(collabPage).toHaveURL(/\/login/)

    await collabPage.getByRole('link', { name: 'Create one' }).click()
    await expect(collabPage).toHaveURL(/\/register/)

    await collabPage.getByPlaceholder('Jane Doe').fill('E2E Collaborator')
    await collabPage.locator('input[type="email"]').fill(collaboratorEmail)
    await collabPage.locator('input[type="password"]').fill(password)
    await collabPage.getByRole('button', { name: 'Create account' }).click()

    await expect(collabPage).toHaveURL(/\/projects\/[0-9a-f-]+$/)
    await expect(collabPage.getByRole('heading', { name: shareProjectName })).toBeVisible()

    await collabContext.close()
  })

  test('the accepted collaborator shows up as a Member for the owner', async () => {
    await page.reload()
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })

    const collaboratorRow = modal.locator('[data-testid="access-row"]').filter({ hasText: 'E2E Collaborator' })
    await expect(collaboratorRow.getByText('Member')).toBeVisible()
  })

  test('the owner row offers profile and email actions instead of removal', async () => {
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    const ownerRow = modal.locator('[data-testid="access-row"]').filter({ hasText: 'Owner' })
    await ownerRow.getByLabel('Owner actions').click()
    await page.getByRole('menuitem', { name: 'View Profile' }).click()

    await expect(page.getByText('Profile view is coming soon.')).toBeVisible()
  })

  test('re-inviting an existing collaborator shows an error toast', async () => {
    await page.getByPlaceholder('name@example.com').fill(collaboratorEmail)
    await page.getByRole('button', { name: 'Invite', exact: true }).click()

    await expect(page.getByLabel(/Notifications/).getByText(/already a member/i)).toBeVisible()
  })

  test('cancels the original pending email invitation', async () => {
    const row = page.locator('[data-testid="pending-invitation-row"]').filter({ hasText: collaboratorEmail })
    await row.getByLabel(`Actions for ${collaboratorEmail}`).click()
    await page.getByRole('menuitem', { name: 'Cancel Invitation' }).click()

    await page.getByRole('button', { name: 'Cancel invitation' }).click()
    await expect(page.getByText('Invitation cancelled')).toBeVisible()
  })

  test('removes the collaborator from the project', async () => {
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    const collaboratorRow = modal.locator('[data-testid="access-row"]').filter({ hasText: 'E2E Collaborator' })
    await collaboratorRow.getByLabel(/Actions for E2E Collaborator/).click()
    await page.getByRole('menuitem', { name: 'Remove from Project' }).click()

    await page.getByRole('dialog', { name: 'Remove collaborator' }).getByRole('button', { name: 'Remove' }).click()
    await expect(page.getByText('Collaborator removed')).toBeVisible()
    await expect(modal.locator('[data-testid="access-row"]').filter({ hasText: 'E2E Collaborator' })).toHaveCount(0)

    await page.keyboard.press('Escape')
  })

  test('archive is a working placeholder that shows a toast', async () => {
    await page.getByRole('button', { name: 'Project actions' }).click()
    await page.getByRole('menuitem', { name: 'Archive Project' }).click()
    await expect(page.getByText('Archiving is coming soon.')).toBeVisible()
  })

  test('deletes the project from the detail page and redirects to the list', async () => {
    await page.getByRole('button', { name: 'Project actions' }).click()
    await page.getByRole('menuitem', { name: 'Delete Project' }).click()
    await page.getByRole('button', { name: 'Delete project' }).click()

    await expect(page).toHaveURL(/\/projects$/)
    await expect(page.getByText('Project deleted')).toBeVisible()
    await expect(page.locator('[data-testid="project-card"]', { hasText: shareProjectName })).toHaveCount(0)
  })

  test('creates a second project and deletes it from the card menu', async () => {
    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(cardDeleteProjectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await expect(page.getByText(`"${cardDeleteProjectName}" was created`)).toBeVisible()

    await page.goto('/projects')
    const card = page.locator('[data-testid="project-card"]', { hasText: cardDeleteProjectName })
    await expect(card).toBeVisible()

    await card.getByRole('button', { name: 'Project actions' }).click()
    await page.getByRole('menuitem', { name: 'Delete' }).click()
    await page.getByRole('button', { name: 'Delete project' }).click()

    await expect(page.getByText('Project deleted')).toBeVisible()
    await expect(page.locator('[data-testid="project-card"]', { hasText: cardDeleteProjectName })).toHaveCount(0)
  })
})
