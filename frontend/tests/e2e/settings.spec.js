import { test, expect } from '@playwright/test'

const run = Date.now()

test.describe('Settings', () => {
  test('updates the profile name and changes the password', async ({ page }) => {
    const email = `settings-e2e-${run}@example.com`

    await page.goto('/register')
    await page.getByPlaceholder('Jane Doe').fill('Settings Owner')
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('secret123')
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.getByRole('link', { name: 'Settings' }).click()
    await expect(page).toHaveURL(/\/settings/)

    await page.locator('input').first().fill('Renamed Owner')
    await page.getByRole('button', { name: 'Save Changes' }).click()
    await expect(page.getByText('Profile updated')).toBeVisible()

    // The Topbar profile menu reflects the change immediately (refreshUser()).
    await expect(page.getByText('Renamed Owner')).toBeVisible()

    const passwordInputs = page.locator('input[type="password"]')
    await passwordInputs.nth(0).fill('secret123')
    await passwordInputs.nth(1).fill('newsecret456')
    await passwordInputs.nth(2).fill('newsecret456')
    await page.getByRole('button', { name: 'Change Password' }).click()
    await expect(page.getByText('Password changed')).toBeVisible()

    // Log out and back in with the new password to prove it actually took.
    await page.getByText('Renamed Owner').click()
    await page.getByRole('button', { name: 'Log out' }).click()
    await expect(page).toHaveURL(/\/login/)

    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill('newsecret456')
    await page.getByRole('button', { name: 'Sign in' }).click()
    // ProtectedRoute redirects back to whatever page the user was on before
    // being logged out (here, /settings), not always to /dashboard - the
    // real thing being proven is that the new password authenticates at all.
    await expect(page).not.toHaveURL(/\/login/)
  })
})
