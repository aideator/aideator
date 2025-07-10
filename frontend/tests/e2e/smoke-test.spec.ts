import { test, expect } from '@playwright/test';

test.describe('Smoke Test - Basic Functionality', () => {
  test('should load homepage and navigate to streaming interface', async ({ page }) => {
    // Load homepage
    await page.goto('http://localhost:3001');
    
    // Check that page loads
    await expect(page.locator('h1')).toContainText('aideator');
    
    // Check for main CTA button (be more flexible with text)
    const ctaButton = page.locator('button, a').filter({ hasText: /Start.*Generation|Start.*Multi.*Agent/ }).first();
    await expect(ctaButton).toBeVisible();
    
    // Click to navigate to streaming page
    await ctaButton.click();
    
    // Should be on streaming page now
    await expect(page).toHaveURL(/stream/);
    
    // Check for form elements
    await expect(page.locator('input, textarea').first()).toBeVisible();
    
    console.log('✅ Basic navigation and page loading works!');
  });

  test('should display configuration form on streaming page', async ({ page }) => {
    // Go directly to streaming page
    await page.goto('http://localhost:3001/stream');
    
    // Check for GitHub URL input
    const githubInput = page.locator('input[type="url"]');
    await expect(githubInput).toBeVisible();
    
    // Check for prompt textarea
    const promptTextarea = page.locator('textarea');
    await expect(promptTextarea).toBeVisible();
    
    // Check for start button
    const startButton = page.locator('button').filter({ hasText: /Start/ });
    await expect(startButton).toBeVisible();
    
    console.log('✅ Configuration form displays correctly!');
  });

  test('should have proper styling and design system', async ({ page }) => {
    await page.goto('http://localhost:3001');
    
    // Check for aideator branding color (ai-primary)
    const brandedElements = page.locator('[class*="ai-primary"], [style*="#4f46e5"]');
    
    // Check for proper card styling
    const cards = page.locator('[class*="card"], [class*="Card"]');
    
    // At least one branded element should exist
    const brandedCount = await brandedElements.count();
    const cardCount = await cards.count();
    
    expect(brandedCount + cardCount).toBeGreaterThan(0);
    
    console.log('✅ Design system styling is applied!');
  });
});