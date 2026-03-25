import { test, expect } from '@playwright/test';

test.describe('Security Headers', () => {
  test('API returns security headers', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.status()).toBe(200);
    expect(response.headers()['x-content-type-options']).toBe('nosniff');
    expect(response.headers()['x-frame-options']).toBe('DENY');
    expect(response.headers()['x-xss-protection']).toBe('1; mode=block');
  });

  test('API returns request ID header', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.headers()['x-request-id']).toBeTruthy();
  });

  test('health endpoint returns database status', async ({ request }) => {
    const response = await request.get('/health');
    const body = await response.json();

    expect(body.status).toMatch(/healthy|degraded/);
    expect(body.version).toBe('1.0.0');
    expect(body).toHaveProperty('database');
    expect(body).toHaveProperty('pool');
  });

  test('metrics endpoint returns Prometheus format', async ({ request }) => {
    const response = await request.get('/metrics');

    expect(response.status()).toBe(200);
    const text = await response.text();
    expect(text).toContain('reconix_http_requests_total');
    expect(text).toContain('reconix_http_active_requests');
  });

  test('unauthenticated API requests are rejected', async ({ request }) => {
    const response = await request.get('/api/v1/recycled-sims');

    expect(response.status()).toBeGreaterThanOrEqual(401);
    expect(response.status()).toBeLessThan(404);
  });

  test('SQL injection in query params is blocked', async ({ request }) => {
    const response = await request.get(
      "/api/v1/recycled-sims?cleanup_status='; DROP TABLE users; --",
      { headers: { Authorization: 'Bearer fake-token' } }
    );

    expect(response.status()).toBe(400);
  });
});

test.describe('Protected Routes', () => {
  test('dashboard redirects unauthenticated users', async ({ page }) => {
    await page.goto('/dashboard');

    await page.waitForURL(/\/$|\/login/, { timeout: 10000 });
    const url = page.url();
    expect(url).toMatch(/\/$|\/login/);
  });

  test('settings page redirects unauthenticated users', async ({ page }) => {
    await page.goto('/settings');

    await page.waitForURL(/\/$|\/login/, { timeout: 10000 });
    const url = page.url();
    expect(url).toMatch(/\/$|\/login/);
  });
});
