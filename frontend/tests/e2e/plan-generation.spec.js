import { test, expect } from '@playwright/test'

const run = Date.now()

// Every new project requires a schedule before it's usable - fills the
// blocking dialog (Start Date is pre-filled with today) that now appears
// once plan generation settles, before the "was created" confirmation
// becomes reachable. Generous timeout matches the real-Gemini-call case.
async function fillProjectSchedule(page) {
  await expect(page.getByRole('heading', { name: 'Set the Project Schedule' })).toBeVisible({
    timeout: 45_000,
  })
  const deadline = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  await page.locator('input[type="date"]').last().fill(deadline)
  await page.getByRole('button', { name: 'Save Schedule' }).click()
}

test.describe('AI plan generation', () => {
  test('uploading a proposal generates a plan the owner can approve', async ({ page }) => {
    // The per-assertion timeouts below are pointless if the test's own
    // overall timeout (30s globally) cuts it off first - real generation has
    // been observed taking up to ~35s in this environment.
    test.setTimeout(60_000)
    const email = `plan-approve-${run}@example.com`
    const projectName = `Plan Approve Project ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Plan Approve Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page
      .getByPlaceholder('What is this project about?')
      .fill('A project created by an automated Playwright test.')
    await page.locator('input[type="file"]').setInputFiles({
      name: 'proposal.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Build a traffic prediction dashboard for a city transit authority.'),
    })
    await expect(page.getByText('Selected: proposal.txt')).toBeVisible()
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()

    // Whether this environment has a real GEMINI_API_KEY (a real Gemini call,
    // observed taking 15-35s with thinking mode's now-unavoidable token
    // overhead - see llm.py) or none (the near-instant FakePlanningOrchestrator
    // fallback) isn't something this spec controls or should assume either way
    // - both are valid dev configurations, so every assertion that depends on
    // generation actually finishing gets a timeout generous enough for the
    // slower real-API case.
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible({ timeout: 45_000 })
    await expect(
      page.getByText('Your AI Project Manager generated an initial plan from your specification.'),
    ).toBeVisible({ timeout: 45_000 })

    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    await page.getByRole('link', { name: 'View Plan' }).click()
    await expect(page).toHaveURL(/\/progress$/)

    const banner = page.getByText('AI-generated plan awaiting your review')
    await expect(banner).toBeVisible()
    // At least one real milestone rendered - specific titles vary between the
    // fake fallback's fixed canned plan and a real generation, so this checks
    // the empty state is gone rather than asserting on either one's content.
    await expect(page.getByText('No milestones yet for this project.')).toHaveCount(0)

    await page.getByRole('button', { name: 'Approve', exact: true }).click()
    await expect(page.getByText('Plan approved')).toBeVisible()
    await expect(banner).toHaveCount(0)
    await expect(page.getByText('No milestones yet for this project.')).toHaveCount(0)
  })

  test('rejecting a generated plan deletes its milestones and resets it to draft', async ({ page }) => {
    test.setTimeout(60_000)
    const email = `plan-reject-${run}@example.com`
    const projectName = `Plan Reject Project ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Plan Reject Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'proposal.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Build an inventory tracking system for a small warehouse.'),
    })
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    // See the timing note in the previous test - this environment's real or
    // fake orchestrator status determines whether this takes ~1s or ~35s.
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible({ timeout: 45_000 })

    await page.getByRole('link', { name: 'Go to Project' }).click()
    await page.getByRole('link', { name: 'View Plan' }).click()
    await expect(page).toHaveURL(/\/progress$/)

    await expect(page.getByText('AI-generated plan awaiting your review')).toBeVisible({
      timeout: 45_000,
    })
    await page.getByRole('button', { name: 'Reject', exact: true }).click()
    await page
      .getByRole('dialog', { name: 'Reject this plan' })
      .getByRole('button', { name: 'Reject plan' })
      .click()

    await expect(page.getByText('Plan rejected')).toBeVisible()
    await expect(page.getByText('AI-generated plan awaiting your review')).toHaveCount(0)
    await expect(page.getByText('No milestones yet for this project.')).toBeVisible()
  })
})
