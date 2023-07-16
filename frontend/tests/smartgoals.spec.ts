import { expect, test } from '@playwright/test';

test('page loads', async ({ page }) => {
  await page.goto('/smartgoals');
  await expect(page.locator('#navbar')).toBeVisible();
});

test('navbar link is active', async ({ page }) => {
  await page.goto('/smartgoals');
  await expect(page.getByRole('link', { name: /smart goals/ })).toHaveClass('active');
});
