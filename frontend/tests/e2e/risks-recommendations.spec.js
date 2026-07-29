import { test, expect } from '@playwright/test'

const run = Date.now()

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

test.describe('Risks, Recommendations, and the Dashboard project filter', () => {
  test('a fresh project shows empty states on its Risks and Recommendations pages', async ({
    page,
  }) => {
    const email = `risk-empty-${run}@example.com`
    const projectName = `Risk Empty Project ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Risk Empty Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()
    await page.getByRole('link', { name: 'Go to Project' }).click()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    // The schedule was already set during creation, so Risk Analysis and
    // Recommendations are reachable directly - no gate in the way.
    await page.getByRole('link', { name: 'View Risks' }).click()
    await expect(page).toHaveURL(/\/risks$/)
    await expect(page.getByRole('heading', { name: 'Risk Analysis' })).toBeVisible()
    await expect(
      page.getByText('No risks detected yet. CapstonePilot monitors this project automatically'),
    ).toBeVisible()

    await page.goBack()
    await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/)

    await page.getByRole('link', { name: 'View Recommendations' }).click()
    await expect(page).toHaveURL(/\/recommendations$/)
    await expect(page.getByRole('heading', { name: 'Recommendations' })).toBeVisible()
    await expect(
      page.getByText('No recommendations yet. CapstonePilot monitors this project automatically'),
    ).toBeVisible()
  })

  test('the dashboard project filter switches between all projects and one project in place', async ({
    page,
  }) => {
    const email = `dash-filter-${run}@example.com`
    const projectName = `Dashboard Filter Project ${run}`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Dashboard Filter Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/projects/new')
    await page.getByPlaceholder('ML-Based Traffic Optimization').fill(projectName)
    await page.getByRole('button', { name: 'Generate AI Project Plan' }).click()
    await fillProjectSchedule(page)
    await expect(page.getByText(`"${projectName}" was created`)).toBeVisible()

    await page.goto('/dashboard')
    const filterButton = page.getByRole('button', { name: 'All Projects' })
    await expect(filterButton).toBeVisible()

    await filterButton.click()
    await page.getByRole('menuitem', { name: projectName }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('button', { name: projectName })).toBeVisible()

    await page.getByRole('button', { name: projectName }).click()
    await page.getByRole('menuitem', { name: 'All Projects' }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('button', { name: 'All Projects' })).toBeVisible()
  })
})
