import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('login page renders with email and password fields', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('login page has no demo credentials exposed', async ({ page }) => {
    await page.goto('/');

    const content = await page.textContent('body');
    expect(content).not.toContain('demo@');
    expect(content).not.toContain('password123');
  });

  test('empty form submission shows validation errors', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByText(/email/i)).toBeVisible();
  });

  test('invalid credentials show error message', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('Email Address').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpassword12');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(
      page.getByText(/invalid|error|failed/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test('password field is type=password', async ({ page }) => {
    await page.goto('/');

    const passwordInput = page.getByLabel('Password');
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('form uses autocomplete attributes', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByLabel('Email Address')).toHaveAttribute('autoComplete', 'email');
    await expect(page.getByLabel('Password')).toHaveAttribute('autoComplete', 'current-password');
  });
});
