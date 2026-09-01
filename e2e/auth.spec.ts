import { test, expect } from '@playwright/test';

test.describe('Authentication & Session E2E Flows', () => {
  test('should render the login page with all standard inputs and links', async ({ page }) => {
    await page.goto('/auth/login');

    await expect(page).toHaveTitle(/Sign in|EAIMOS|Viptant/i);
    await expect(page.locator('#login-email')).toBeVisible();
    await expect(page.locator('#login-password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('a[href="/auth/register"]')).toBeVisible();
    await expect(page.locator('a[href="/auth/forgot-password"]')).toBeVisible();
  });

  test('should reject invalid credentials with a safe user-facing error message', async ({ page }) => {
    await page.goto('/auth/login');

    await page.fill('#login-email', 'nonexistent_e2e_user@example.com');
    await page.fill('#login-password', 'WrongPassword123!');
    await page.click('button[type="submit"]');

    // Verify safe error notification is shown without leaking server internals
    const errorAlert = page.locator('text=Incorrect email or password').or(page.locator('text=Authentication Failed'));
    await expect(errorAlert.first()).toBeVisible({ timeout: 10000 });
  });

  test('should validate registration inputs and password match client-side', async ({ page }) => {
    await page.goto('/auth/register');

    await page.fill('input[name="fullName"]', 'Test E2E User');
    await page.fill('input[name="email"]', 'e2e_register_test@example.com');
    await page.fill('input[name="orgName"]', 'Test Org');
    await page.fill('input[name="password"]', 'Password123!');
    await page.fill('input[name="confirmPassword"]', 'MismatchPassword456!');
    await page.click('button[type="submit"]');

    // Verify client-side validation errors trigger
    const validationError = page.locator('text=Passwords do not match').or(page.locator('text=Invalid email address'));
    await expect(validationError.first()).toBeVisible();
  });

  test('should navigate seamlessly between all authentication lifecycle screens', async ({ page }) => {
    // 1. Forgot password
    await page.goto('/auth/login');
    await page.click('a[href="/auth/forgot-password"]');
    await expect(page).toHaveURL(/\/auth\/forgot-password/);
    await expect(page.locator('input[type="email"]')).toBeVisible();

    // 2. Restore account
    await page.goto('/auth/restore-account');
    await expect(page).toHaveURL(/\/auth\/restore-account/);

    // 3. Register
    await page.goto('/auth/register');
    await expect(page).toHaveURL(/\/auth\/register/);
  });

  test('should redirect unauthenticated access to protected dashboard routes to login', async ({ page }) => {
    await page.goto('/dashboard');
    // Next.js middleware or client guard redirects unauthenticated users
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
