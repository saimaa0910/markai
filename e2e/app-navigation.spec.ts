import { test, expect } from '@playwright/test';

test.describe('Core Application Navigation & Public Journeys', () => {
  test('should render the landing page with complete brand assets and navigation', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Viptant|EAIMOS|Marketing/i);
    // Verify header and primary call-to-action exist
    const cta = page.locator('a[href="/auth/register"]').or(page.locator('a[href="/auth/login"]'));
    await expect(cta.first()).toBeVisible();
  });

  test('should navigate to legal and compliance pages successfully', async ({ page }) => {
    await page.goto('/legal/terms');
    await expect(page.locator('h1').or(page.locator('main'))).toBeVisible();

    await page.goto('/legal/privacy-policy');
    await expect(page.locator('h1').or(page.locator('main'))).toBeVisible();

    await page.goto('/legal/security');
    await expect(page.locator('h1').or(page.locator('main'))).toBeVisible();
  });

  test('should navigate to developer documentation routes', async ({ page }) => {
    await page.goto('/developers/api-docs');
    await expect(page.locator('h1').or(page.locator('main'))).toBeVisible();
  });
});
