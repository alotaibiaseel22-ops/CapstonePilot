import { test, expect } from '@playwright/test'

const run = Date.now()
const API = 'http://localhost:9000/api/v1'

test.describe('Real activity feed and notifications bell', () => {
  test('completing a task shows up in the Dashboard feed and clears the bell after opening', async ({
    page,
  }) => {
    const email = `activity-e2e-${run}@example.com`
    const projectName = `Activity E2E Project ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Activity Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    // A brand-new user with no projects yet starts with a clean bell.
    const notificationsButton = page.getByRole('button', { name: 'Notifications' })
    await expect(notificationsButton.locator('span.bg-red-500')).toHaveCount(0)

    // Set up the project/milestone/task/completion directly against the API
    // (not through the AI Planner's upload flow) - this spec is testing the
    // activity feed and bell's real rendering, not the Planner's own latency
    // (already covered by plan-generation.spec.js), so it stays fast and
    // deterministic regardless of whether a real Gemini key is configured in
    // this environment.
    const token = await page.evaluate(() => localStorage.getItem('capstonepilot_token'))
    const headers = { Authorization: `Bearer ${token}` }

    const project = await (
      await page.request.post(`${API}/projects`, {
        headers,
        data: { name: projectName, description: 'An e2e test project.' },
      })
    ).json()
    const milestone = await (
      await page.request.post(`${API}/projects/${project.id}/milestones`, {
        headers,
        data: { title: 'Milestone One' },
      })
    ).json()
    const task = await (
      await page.request.post(`${API}/milestones/${milestone.id}/tasks`, {
        headers,
        data: { title: 'Write the report' },
      })
    ).json()
    await page.request.patch(`${API}/tasks/${task.id}`, { headers, data: { status: 'done' } })

    await page.goto('/dashboard')
    await expect(page.getByText('Recent Activity')).toBeVisible()
    await expect(page.getByText('Activity Owner completed "Write the report"')).toBeVisible()
    await expect(page.getByText('Activity Owner created the project')).toBeVisible()

    await expect(notificationsButton.locator('span.bg-red-500')).toBeVisible()
    await notificationsButton.click()
    await expect(page.getByText('RECENT ACTIVITY', { exact: true })).toBeVisible()
    await expect(notificationsButton.locator('span.bg-red-500')).toHaveCount(0)
  })
})
