import { test, expect } from '@playwright/test';

test.describe('AIdeator Homepage', () => {
  test('should load homepage with correct title and branding', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/AIdeator/);

    // Check main heading
    await expect(page.locator('h1')).toContainText('AIdeator');

    // Check subtitle/description
    await expect(page.locator('text=Kubernetes-native LLM orchestration platform')).toBeVisible();

    // Check hero section
    await expect(page.locator('text=Multi-Agent AI')).toBeVisible();
    await expect(page.locator('text=Orchestration')).toBeVisible();
  });

  test('should have working navigation to streaming interface', async ({ page }) => {
    await page.goto('/');

    // Click the main CTA button
    const ctaButton = page.locator('text=Start Multi-Agent Generation').first();
    await expect(ctaButton).toBeVisible();
    
    await ctaButton.click();

    // Should navigate to /stream
    await expect(page).toHaveURL('/stream');
    
    // Check that streaming page loaded
    await expect(page.locator('text=Generation Configuration')).toBeVisible();
  });

  test('should display feature cards', async ({ page }) => {
    await page.goto('/');

    // Check feature cards are visible
    await expect(page.locator('text=Parallel Processing')).toBeVisible();
    await expect(page.locator('text=Real-time Streaming')).toBeVisible();
    await expect(page.locator('text=Enterprise Ready')).toBeVisible();

    // Check feature descriptions
    await expect(page.locator('text=Run up to 5 AI agents simultaneously')).toBeVisible();
    await expect(page.locator('text=Watch agents think and work in real-time')).toBeVisible();
    await expect(page.locator('text=Built on Kubernetes')).toBeVisible();
  });

  test('should display how it works section', async ({ page }) => {
    await page.goto('/');

    // Check the steps
    await expect(page.locator('text=Configure Task')).toBeVisible();
    await expect(page.locator('text=Watch Agents Work')).toBeVisible();
    await expect(page.locator('text=Select Best Result')).toBeVisible();

    // Check step numbers
    await expect(page.locator('text=1').first()).toBeVisible();
    await expect(page.locator('text=2').first()).toBeVisible();
    await expect(page.locator('text=3').first()).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check that content is still visible and properly laid out
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text=Start Multi-Agent Generation').first()).toBeVisible();
    
    // Feature cards should stack vertically on mobile
    const featureCards = page.locator('[class*="grid"]').filter({ hasText: 'Parallel Processing' });
    await expect(featureCards).toBeVisible();
  });

  test('should have accessible design system colors', async ({ page }) => {
    await page.goto('/');

    // Check that brand colors are applied
    const logo = page.locator('[class*="text-ai-primary"]').first();
    await expect(logo).toBeVisible();

    // Check that CTA buttons have proper styling
    const primaryButton = page.locator('[class*="bg-ai-primary"]').first();
    await expect(primaryButton).toBeVisible();
  });
});