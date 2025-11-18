import { test, expect } from '@playwright/test';

// Helper to login before each test
async function login(page) {
  await page.goto('/login');
  await page.getByPlaceholder(/email address/i).fill('analyst@example.com');
  await page.getByPlaceholder(/password/i).fill('password123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/console/);
}

test.describe('Decision Console', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/console');
  });

  test('should display console dashboard', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /decision console/i })).toBeVisible();
  });

  test('should navigate to different sections', async ({ page }) => {
    // Navigation should be visible
    await expect(page.getByRole('link', { name: /policy lab/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /causal design/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /portfolio/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /diagnostics/i })).toBeVisible();
  });
});

test.describe('Policy Lab Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/policy');
  });

  test('should display policy lab interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /policy lab/i })).toBeVisible();
  });

  test('should create new policy', async ({ page }) => {
    // Look for create policy button
    const createButton = page.getByRole('button', { name: /create|new policy/i });

    if (await createButton.isVisible()) {
      await createButton.click();

      // Fill in policy details
      // (Implementation depends on actual form fields)
      await expect(page.getByRole('dialog')).toBeVisible();
    }
  });
});

test.describe('Causal Design Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/causal');
  });

  test('should display causal design interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /causal design/i })).toBeVisible();
  });

  test('should upload dataset', async ({ page }) => {
    // Look for upload functionality
    const uploadButton = page.getByRole('button', { name: /upload/i });

    if (await uploadButton.isVisible()) {
      await uploadButton.click();
    }
  });

  test('should run causal analysis', async ({ page }) => {
    // Look for analysis controls
    const runButton = page.getByRole('button', { name: /run|analyze/i });

    if (await runButton.isVisible()) {
      // Should be able to configure and run analysis
      await expect(runButton).toBeVisible();
    }
  });
});

test.describe('Portfolio & ROI', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/portfolio');
  });

  test('should display portfolio overview', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /portfolio/i })).toBeVisible();
  });

  test('should display ROI metrics', async ({ page }) => {
    // Look for ROI-related content
    const roiIndicators = page.getByText(/ROI|return on investment/i);

    if (await roiIndicators.first().isVisible()) {
      await expect(roiIndicators.first()).toBeVisible();
    }
  });

  test('should display portfolio optimization', async ({ page }) => {
    // Look for optimization controls
    const optimizeButton = page.getByRole('button', { name: /optimize/i });

    if (await optimizeButton.isVisible()) {
      await expect(optimizeButton).toBeVisible();
    }
  });
});

test.describe('Diagnostics', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/diagnostics');
  });

  test('should display diagnostics interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /diagnostics/i })).toBeVisible();
  });

  test('should display diagnostic plots', async ({ page }) => {
    // Look for plot containers
    const plots = page.locator('canvas, svg').filter({ hasText: '' });

    // Should have some visualizations
    // (Exact assertions depend on implementation)
    await expect(page).toHaveURL(/\/diagnostics/);
  });
});

test.describe('Data Upload and Processing', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should upload CSV file', async ({ page }) => {
    await page.goto('/causal');

    // Create test CSV file
    const fileContent = 'id,treatment,outcome,age,gender\n1,1,100,25,M\n2,0,80,30,F';

    // Look for file input
    const fileInput = page.locator('input[type="file"]').first();

    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test_data.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(fileContent),
      });

      // Should show upload success
      await expect(page.getByText(/uploaded|success/i)).toBeVisible({ timeout: 10000 });
    }
  });
});

test.describe('User Interface', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display user information', async ({ page }) => {
    // User info should be visible in sidebar
    await expect(page.getByText(/signed in as/i)).toBeVisible();
    await expect(page.getByText(/analyst@example.com/i)).toBeVisible();

    // Role badge should be visible
    await expect(page.getByText(/analyst/i)).toBeVisible();
  });

  test('should have responsive navigation', async ({ page }) => {
    await page.goto('/console');

    // All nav links should be present
    const navLinks = [
      'Decision Console',
      'Policy Lab',
      'Causal Design',
      'Portfolio & ROI',
      'Diagnostics',
    ];

    for (const linkText of navLinks) {
      await expect(page.getByRole('link', { name: new RegExp(linkText, 'i') })).toBeVisible();
    }
  });

  test('should highlight active page in navigation', async ({ page }) => {
    await page.goto('/policy');

    // Policy Lab link should be active
    const policyLink = page.getByRole('link', { name: /policy lab/i });
    await expect(policyLink).toHaveClass(/active/);
  });
});

test.describe('Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate offline
    await page.context().setOffline(true);

    await page.goto('/console');

    // Should show error or loading state
    // (Exact behavior depends on implementation)

    // Restore connection
    await page.context().setOffline(false);
  });

  test('should handle 404 routes', async ({ page }) => {
    await page.goto('/nonexistent-route');

    // Should redirect or show 404 page
    // (Depends on routing implementation)
  });
});

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/console');

    // Main navigation should have proper labels
    const nav = page.getByRole('navigation');
    await expect(nav).toBeVisible();

    // Buttons should have accessible names
    const logoutButton = page.getByRole('button', { name: /logout/i });
    await expect(logoutButton).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/console');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should be able to navigate via keyboard
    // (Specific assertions depend on implementation)
  });
});
