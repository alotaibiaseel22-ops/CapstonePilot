import { test, expect } from '@playwright/test'

const run = Date.now()

test.describe('registration error handling', () => {
  test('duplicate email shows the real backend message, not a generic one', async ({ page }) => {
    const email = `dup-${run}@example.com`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('First Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    // Log out (clear the session token) and try registering the same email again.
    await page.evaluate(() => localStorage.removeItem('capstonepilot_token'))
    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Second Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()

    await expect(page.getByText(`${email} is already registered`)).toBeVisible()
    await expect(page.getByText('Could not create your account. Please try again.')).toHaveCount(0)
  })

  test('an unreachable backend shows a network message, not a generic one', async ({ page }) => {
    await page.route('**/api/v1/auth/register', (route) => route.abort('failed'))

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Offline User')
    await page.locator('input[type="email"]').fill(`offline-${run}@example.com`)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()

    await expect(page.getByText(/Could not reach the server/i)).toBeVisible()
    await expect(page.getByText('Could not create your account. Please try again.')).toHaveCount(0)
  })

  test('password shorter than 8 characters is blocked before submitting', async ({ page }) => {
    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Short Pw User')
    await page.locator('input[type="email"]').fill(`shortpw-${run}@example.com`)
    const passwordInput = page.locator('input[type="password"]')
    await passwordInput.fill('abc')
    await page.getByRole('button', { name: 'Create account' }).click()

    // Native HTML5 minlength validation should keep us on the register page
    // (no navigation, no API call fired) rather than surfacing a server error.
    await expect(page).toHaveURL(/\/register/)
    const isValid = await passwordInput.evaluate((el) => el.checkValidity())
    expect(isValid).toBe(false)
  })
})
