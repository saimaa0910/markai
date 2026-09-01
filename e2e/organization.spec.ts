import { test, expect } from '@playwright/test';

test.describe('Organization Context & IAM E2E Scenarios', () => {
  test('should enforce protected route boundary for organization settings', async ({ page }) => {
    // Attempting to access settings without authentication redirects to login
    await page.goto('/dashboard/settings/organization');
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('should enforce protected route boundary for member management', async ({ page }) => {
    await page.goto('/dashboard/settings/members');
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('should enforce protected route boundary for security & credentials', async ({ page }) => {
    await page.goto('/dashboard/settings/security');
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
