import { test, expect } from '@playwright/test';

test.describe('ChatGPT-style Layout Tests', () => {
  test('should display ChatGPT-style interface elements', async ({ page }) => {
    await page.goto('/stream');

    // Check that the page loads without the old header
    await expect(page.locator('h1')).toContainText('aideator');
    
    // Verify welcome message is in conversation area (not in header)
    await expect(page.locator('text=Multi-Model Prompt Comparison Platform')).toBeVisible();

    // Check bottom fixed input area
    await expect(page.locator('textarea')).toBeVisible();
    await expect(page.locator('textarea')).toHaveAttribute('placeholder', /Ask a question/);

    // Check settings toggle
    await expect(page.locator('text=Show Settings')).toBeVisible();

    // Verify no old accordion modal structure
    await expect(page.locator('text=Model Comparison Configuration')).toHaveCount(0);
  });

  test('should have proper ChatGPT-style scrolling layout', async ({ page }) => {
    await page.goto('/stream');

    // Check conversation container is scrollable
    const conversationArea = page.locator('[class*="flex-1"][class*="overflow-y-auto"]');
    await expect(conversationArea).toBeVisible();

    // Check input is fixed at bottom
    const bottomInput = page.locator('[class*="fixed"][class*="bottom-0"]');
    await expect(bottomInput).toBeVisible();

    // Verify layout structure
    await expect(page.locator('[class*="h-full"][class*="flex"][class*="flex-col"][class*="overflow-hidden"]')).toBeVisible();
  });

  test('should toggle settings panel in bottom input area', async ({ page }) => {
    await page.goto('/stream');

    // Initially settings should be collapsed
    await expect(page.locator('text=Show Settings')).toBeVisible();

    // Click to show settings
    await page.locator('text=Show Settings').click();

    // Settings content should appear
    await expect(page.locator('text=Hide Settings')).toBeVisible();

    // Click to hide settings
    await page.locator('text=Hide Settings').click();

    // Should be back to show settings
    await expect(page.locator('text=Show Settings')).toBeVisible();
  });
});