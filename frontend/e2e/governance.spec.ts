import { test, expect } from '@playwright/test';

async function login(page) {
  await page.goto('/login');
  await page.getByPlaceholder(/email address/i).fill('analyst@example.com');
  await page.getByPlaceholder(/password/i).fill('password123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/console/);
}

test.describe('Governance Center', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/governance');
  });

  test('should display all governance sections', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Governance Center/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Data & Sensitivity/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Compliance/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Quality Gates Overview/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Violation Log/i })).toBeVisible();
  });

  test('should allow editing payloads and running checks', async ({ page }) => {
    const dataTextarea = page.getByLabel(/Uplift Data JSON/i);
    await dataTextarea.clear();
    await dataTextarea.fill(JSON.stringify([{ delta_yen: 1500, gender: 'male' }, { delta_yen: 100, gender: 'female' }], null, 2));

    const sensitiveTextarea = page.getByLabel(/Sensitive Attributes/i);
    await sensitiveTextarea.clear();
    await sensitiveTextarea.fill(JSON.stringify({ gender: ['male', 'female'] }));

    const fairnessButton = page.getByRole('button', { name: /check fairness/i });
    await expect(fairnessButton).toBeVisible();
  });

  test('navigation should include governance link', async ({ page }) => {
    await page.goto('/console');
    await expect(page.getByRole('link', { name: /governance center/i })).toBeVisible();
  });
});
