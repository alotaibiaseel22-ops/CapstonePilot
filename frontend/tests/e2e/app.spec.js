import { test, expect } from '@playwright/test'

const run = Date.now()
const ownerName = 'E2E Owner'
const ownerEmail = `owner-${run}@example.com`
const ownerPassword = 'secret123'
const collaboratorEmail = `collab-${run}@example.com`
const linkAcceptEmail = `link-accept-${run}@example.com`
const shareProjectName = `Playwright Share Project ${run}`
const cardDeleteProjectName = `Playwright Card Delete Project ${run}`

let shareableLink = ''

// Every new project requires a schedule before it's usable - fills the
// blocking dialog (Start Date is pre-filled with today) that now appears
// right after "Generate AI Project Plan", before the "was created"
// confirmation becomes reachable.
async function fillProjectSchedule(page) {
  await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible()
  const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  await page.locator('input[type="date"]').last().fill(deadline)
  await page.getByRole('button', { name: 'Save Schedule' }).click()
}

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
    await fillProjectSchedule(page)
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

  test('a visitor joins as a guest via the shareable link - no account, no login', async ({ browser }) => {
    // The whole point of the shareable link (Figma/Canva-style access): no
    // email, no password, ever - never redirected to Login or Register.
    expect(shareableLink).toContain('/invite/')
    const guestContext = await browser.newContext()
    const guestPage = await guestContext.newPage()

    await guestPage.goto(shareableLink)
    await expect(guestPage).toHaveURL(/\/guest\//)
    await expect(guestPage.getByLabel('Email', { exact: false })).toHaveCount(0)
    await expect(guestPage.getByLabel('Password', { exact: false })).toHaveCount(0)

    await guestPage.getByPlaceholder('Jane Doe').fill('E2E Guest')
    await guestPage.getByRole('button', { name: 'Continue' }).click()

    await expect(guestPage.getByText(shareProjectName)).toBeVisible()
    await expect(guestPage.getByText('Guest view')).toBeVisible()

    // A second visit with the same link, same browser, resumes the same
    // guest identity instead of prompting for a name again.
    await guestPage.goto(shareableLink)
    await expect(guestPage.getByText(shareProjectName)).toBeVisible()
    await expect(guestPage.getByPlaceholder('Jane Doe')).toHaveCount(0)

    await guestContext.close()
  })

  test('a guest joining via the link never becomes a project Member', async () => {
    await page.reload()
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })

    await expect(modal.locator('[data-testid="access-row"]').filter({ hasText: 'E2E Guest' })).toHaveCount(0)
    await page.keyboard.press('Escape')
  })

  test('a separate email invite is still accepted as a full member, shown on the Share dialog', async ({
    browser,
  }) => {
    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await page.getByPlaceholder('name@example.com').fill(linkAcceptEmail)
    await page.getByRole('button', { name: 'Invite', exact: true }).click()
    await expect(page.getByText(`Invitation sent to ${linkAcceptEmail}`)).toBeVisible()

    const row = modal.locator('[data-testid="pending-invitation-row"]').filter({ hasText: linkAcceptEmail })
    await row.getByLabel(`Actions for ${linkAcceptEmail}`).click()
    await page.getByRole('menuitem', { name: 'Copy Invite Link' }).click()
    const linkAcceptInviteLink = await page.evaluate(() => navigator.clipboard.readText())
    expect(linkAcceptInviteLink).toContain('/invite/')
    await page.keyboard.press('Escape')

    const collabContext = await browser.newContext()
    const collabPage = await collabContext.newPage()
    await collabPage.goto(linkAcceptInviteLink)
    await expect(collabPage.getByRole('heading', { name: `Join ${shareProjectName}` })).toBeVisible()
    await collabPage.getByPlaceholder('Jane Doe').fill('E2E Collaborator')
    await collabPage.getByRole('button', { name: 'Join Project' }).click()
    await expect(collabPage).toHaveURL(/\/projects\/[0-9a-f-]+$/)
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

    const profileDialog = page.getByRole('dialog', { name: 'Profile' })
    await expect(profileDialog.getByText(ownerName)).toBeVisible()
    await expect(profileDialog.getByText(ownerEmail)).toBeVisible()
    await expect(profileDialog.getByText('Owner', { exact: true })).toBeVisible()
    // Close via the dialog's own X, not Escape - the underlying Share
    // dialog is still open too and also listens for Escape, which would
    // close both at once and break the next test's use of it.
    await profileDialog.getByLabel('Close').click()
    await expect(profileDialog).toHaveCount(0)
  })

  test('re-inviting an existing collaborator shows an error toast', async () => {
    // linkAcceptEmail, not collaboratorEmail - that invitation was accepted
    // (see "a separate email invite is still accepted..." above), so it's
    // the one that's actually a member now. collaboratorEmail's own
    // invitation is still sitting pending, untouched, for the next test.
    await page.getByPlaceholder('name@example.com').fill(linkAcceptEmail)
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

  test('archiving a project sets its status and can be undone', async () => {
    // Asserting on the banner/badge state, not the "Project updated" toast -
    // two of the same toast stacking (archive, then unarchive) makes that
    // text ambiguous/flaky to assert on twice in one test.
    await page.getByRole('button', { name: 'Project actions' }).click()
    await page.getByRole('menuitem', { name: 'Archive Project' }).click()
    await expect(page.getByText('This project is archived.')).toBeVisible()
    await expect(page.getByText('Archived', { exact: true })).toBeVisible()

    await page.getByRole('button', { name: 'Project actions' }).click()
    await page.getByRole('menuitem', { name: 'Unarchive Project' }).click()
    await expect(page.getByText('This project is archived.')).toHaveCount(0)
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
    await fillProjectSchedule(page)
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

  test('a new collaborator joins directly via an email invite with just their name', async ({ browser }) => {
    const onboardProjectName = `Playwright Onboard Project ${run}`
    const onboardEmail = `onboard-${run}@example.com`
    const onboardName = 'E2E Onboarded'

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(onboardProjectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${onboardProjectName}" was created`)).toBeVisible()
    await page.getByRole('link', { name: 'Go to Project' }).click()

    await page.getByRole('button', { name: 'Share' }).click()
    const modal = page.getByRole('dialog', { name: 'Share Project' })
    await page.getByPlaceholder('name@example.com').fill(onboardEmail)
    await page.getByRole('button', { name: 'Invite', exact: true }).click()
    await expect(page.getByText(`Invitation sent to ${onboardEmail}`)).toBeVisible()

    const row = modal.locator('[data-testid="pending-invitation-row"]').filter({ hasText: onboardEmail })
    await row.getByLabel(`Actions for ${onboardEmail}`).click()
    await page.getByRole('menuitem', { name: 'Copy Invite Link' }).click()
    await expect(page.getByText('Invite link copied')).toBeVisible()
    const inviteLink = await page.evaluate(() => navigator.clipboard.readText())
    expect(inviteLink).toContain('/invite/')
    await page.keyboard.press('Escape')

    // Fresh, unauthenticated context - never should touch Login or Register.
    const onboardContext = await browser.newContext()
    const onboardPage = await onboardContext.newPage()
    await onboardPage.goto(inviteLink)

    await expect(onboardPage.getByRole('heading', { name: `Join ${onboardProjectName}` })).toBeVisible()
    await expect(onboardPage.getByText(`${ownerName} invited you`)).toBeVisible()
    await expect(onboardPage.getByLabel('Email', { exact: false })).toHaveCount(0)
    await expect(onboardPage.getByLabel('Password', { exact: false })).toHaveCount(0)

    await onboardPage.getByPlaceholder('Jane Doe').fill(onboardName)
    await onboardPage.getByRole('button', { name: 'Join Project' }).click()

    await expect(onboardPage).toHaveURL(/\/projects\/[0-9a-f-]+$/)
    await expect(onboardPage.getByRole('heading', { name: onboardProjectName })).toBeVisible()

    await onboardContext.close()
  })
})
