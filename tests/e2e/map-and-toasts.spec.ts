import { test, expect } from '@playwright/test';

test.describe('Map and Toasts', () => {
  test('shows map unavailable toast and no-events info when backend returns empty', async ({ page }) => {
    // Mock backend to return empty events
    await page.route('**/api/events**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ events: [], count: 0, source: 'legistar', generated_at: new Date().toISOString() }),
      });
    });

    await page.goto('/');

    // MapUnavailable toast should appear
    await expect(page.locator('text=Map unavailable')).toBeVisible({ timeout: 5000 });

    // No events info should be visible in the events section
    await expect(page.locator('text=No events match your filters')).toBeVisible();
  });

  test('shows success toast when backend returns events', async ({ page }) => {
    await page.route('**/api/events**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ events: [{ id: '1', title: 'Test Event' }], count: 1, source: 'legistar', generated_at: new Date().toISOString() }),
      });
    });

    await page.goto('/');

    // Success toast
    await expect(page.locator('text=1 events loaded')).toBeVisible({ timeout: 5000 });

    // Event card
    await expect(page.locator('text=Test Event')).toBeVisible();
  });

  test('shows error toast when backend fails', async ({ page }) => {
    await page.route('**/api/events**', async (route) => {
      await route.fulfill({ status: 500, contentType: 'text/plain', body: 'Server error' });
    });

    await page.goto('/');

    await expect(page.locator('text=Failed to load events')).toBeVisible({ timeout: 5000 });
  });
});
