import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveTitle(/CQOx/);
    await expect(page.getByRole('heading', { name: /Causal Query Optimizer/i })).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    const loginButton = page.getByRole('button', { name: /sign in/i });
    await loginButton.click();

    // HTML5 validation should prevent submission
    const emailInput = page.getByPlaceholder(/email address/i);
    await expect(emailInput).toHaveAttribute('required');
  });

  test('should login with valid credentials', async ({ page }) => {
    // Fill in login form
    await page.getByPlaceholder(/email address/i).fill('test@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');

    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/console/);

    // Should show user info
    await expect(page.getByText(/signed in as/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.getByPlaceholder(/email address/i).fill('test@example.com');
    await page.getByPlaceholder(/password/i).fill('wrongpassword');

    await page.getByRole('button', { name: /sign in/i }).click();

    // Should show error message
    await expect(page.getByText(/invalid credentials|login failed/i)).toBeVisible();
  });

  test('should display OAuth login buttons', async ({ page }) => {
    await expect(page.getByRole('button', { name: /google/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /github/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /microsoft/i })).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.getByPlaceholder(/email address/i).fill('test@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page).toHaveURL(/\/console/);

    // Logout
    await page.getByRole('button', { name: /logout/i }).click();

    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Protected Routes', () => {
  test('should redirect to login if not authenticated', async ({ page }) => {
    await page.goto('/console');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should access protected routes after login', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByPlaceholder(/email address/i).fill('analyst@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Navigate to different pages
    await page.getByRole('link', { name: /policy lab/i }).click();
    await expect(page).toHaveURL(/\/policy/);

    await page.getByRole('link', { name: /causal design/i }).click();
    await expect(page).toHaveURL(/\/causal/);

    await page.getByRole('link', { name: /portfolio/i }).click();
    await expect(page).toHaveURL(/\/portfolio/);
  });
});

test.describe('Role-Based Access', () => {
  test('viewer should not access write operations', async ({ page }) => {
    // Login as viewer
    await page.goto('/login');
    await page.getByPlaceholder(/email address/i).fill('viewer@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Try to access policy lab (requires models:write)
    await page.goto('/policy');

    // Should show permission denied or redirect
    await expect(
      page.getByText(/access denied|permission denied/i)
    ).toBeVisible();
  });

  test('analyst should access write operations', async ({ page }) => {
    // Login as analyst
    await page.goto('/login');
    await page.getByPlaceholder(/email address/i).fill('analyst@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should access policy lab
    await page.goto('/policy');
    await expect(page).toHaveURL(/\/policy/);

    // Should not show permission denied
    await expect(
      page.getByText(/access denied|permission denied/i)
    ).not.toBeVisible();
  });

  test('admin should access all routes', async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.getByPlaceholder(/email address/i).fill('admin@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should access all routes
    const routes = ['/console', '/policy', '/causal', '/portfolio', '/diagnostics'];

    for (const route of routes) {
      await page.goto(route);
      await expect(page).toHaveURL(route);
      await expect(
        page.getByText(/access denied|permission denied/i)
      ).not.toBeVisible();
    }
  });
});

test.describe('Token Refresh', () => {
  test('should refresh token automatically', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.getByPlaceholder(/email address/i).fill('test@example.com');
    await page.getByPlaceholder(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page).toHaveURL(/\/console/);

    // Wait for token to be near expiry (mock this in test env)
    // In real scenario, set short token expiry for testing

    // Make API request - should auto-refresh if needed
    await page.reload();

    // Should still be authenticated
    await expect(page).toHaveURL(/\/console/);
    await expect(page.getByText(/signed in as/i)).toBeVisible();
  });
});
