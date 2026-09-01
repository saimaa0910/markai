import { test, expect } from '@playwright/test';

test.describe('Error Handling & Boundary Verification', () => {
  test('should render custom 404 page for nonexistent routes without server leaks', async ({ page }) => {
    await page.goto('/some/unknown/nonexistent-route-12345');
    
    // Check 404 UI is displayed
    const notFoundIndicator = page.locator('text=404').or(page.locator('text=Page Not Found')).or(page.locator('text=not found')).or(page.locator('text=Lost in Orbit'));
    await expect(notFoundIndicator.first()).toBeVisible();

    // Verify raw internal tracebacks are not exposed to the client
    const bodyText = await page.innerText('body');
    expect(bodyText).not.toContain('Traceback (most recent call last)');
    expect(bodyText).not.toContain('Internal Server Error 500');
  });

  test('should render maintenance route cleanly when accessed directly', async ({ page }) => {
    await page.goto('/maintenance');
    const maintenanceIndicator = page.locator('text=System Upgrades').or(page.locator('text=Maintenance')).or(page.locator('text=Updates in Progress')).or(page.locator('text=scheduled optimization'));
    await expect(maintenanceIndicator.first()).toBeVisible();
  });
});
