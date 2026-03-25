import { test, expect } from '@playwright/test';

test.describe('Navigation and UI', () => {
  test('login page loads without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes('favicon') && !e.includes('404')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test('page has correct title', async ({ page }) => {
    await page.goto('/');

    const title = await page.title();
    expect(title.toLowerCase()).toContain('reconix');
  });

  test('login page is responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page.getByLabel('Email Address')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('no broken images on login page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const images = await page.locator('img').all();
    for (const img of images) {
      const naturalWidth = await img.evaluate(
        (el: HTMLImageElement) => el.naturalWidth
      );
      expect(naturalWidth).toBeGreaterThan(0);
    }
  });
});
