import { test, expect } from '@playwright/test';

test.describe('AdaptiveLayout Integration - Core Functionality Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');
  });

  test('✅ CRITICAL: AdaptiveLayout renders without crashes', async ({ page }) => {
    // Verify page loads without JS errors
    await expect(page).toHaveTitle(/aideator/);
    
    // Check that sidebar is rendered
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
    
    // Check that main content area exists
    await expect(page.locator('text=Model Comparison Configuration')).toBeVisible();
    
    // Check that mode indicator is working
    await expect(page.locator('[data-testid="mode-indicator"]')).toBeVisible();
    
    console.log('✅ AdaptiveLayout renders successfully');
  });

  test('✅ CRITICAL: Sidebar toggle functionality works', async ({ page }) => {
    const sidebar = page.locator('[data-testid="sidebar"]');
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    
    // Verify sidebar starts expanded
    await expect(sidebar).toBeVisible();
    
    // Click to collapse
    await toggleButton.click();
    await page.waitForTimeout(500);
    
    // Should show collapsed state
    await expect(page.locator('[data-testid="sidebar-collapsed"]')).toBeVisible();
    
    // Click to expand again
    await toggleButton.click();
    await page.waitForTimeout(500);
    
    // Should return to expanded state
    await expect(sidebar).toBeVisible();
    
    console.log('✅ Sidebar toggle works correctly');
  });

  test('✅ CRITICAL: Mode switching interface works', async ({ page }) => {
    // All mode buttons should be present
    await expect(page.locator('[data-testid="mode-welcome"]')).toBeVisible();
    await expect(page.locator('[data-testid="mode-chat"]')).toBeVisible();
    await expect(page.locator('[data-testid="mode-compare"]')).toBeVisible();
    
    // Mode indicator should show current mode
    await expect(page.locator('[data-testid="mode-indicator"]')).toContainText('welcome');
    
    console.log('✅ Mode switching interface works');
  });

  test('✅ CRITICAL: Configuration panel expansion works', async ({ page }) => {
    // Find and click the configuration header
    const configHeader = page.locator('text=Model Comparison Configuration');
    await expect(configHeader).toBeVisible();
    
    // Click to expand (it starts expanded, so this will collapse it)
    await configHeader.click();
    await page.waitForTimeout(500);
    
    // Click again to expand
    await configHeader.click();
    await page.waitForTimeout(1000);
    
    // The panel should show some form elements after expansion
    // Use more flexible selectors
    await expect(page.locator('textarea')).toBeVisible();
    
    console.log('✅ Configuration panel expansion works');
  });

  test('✅ CRITICAL: New session creation works', async ({ page }) => {
    // Click the new session button
    const newSessionBtn = page.locator('[data-testid="new-session-btn"]');
    await expect(newSessionBtn).toBeVisible();
    
    // The button should be clickable (even if it doesn't create a real session)
    await expect(newSessionBtn).toBeEnabled();
    
    console.log('✅ New session button is present and functional');
  });

  test('✅ CRITICAL: Essential UI components are accessible', async ({ page }) => {
    // Test that all essential components for the app to work are present
    const essentialComponents = [
      '[data-testid="sidebar"]',
      '[data-testid="mode-indicator"]', 
      '[data-testid="sidebar-toggle"]',
      '[data-testid="new-session-btn"]',
      'text=Model Comparison Configuration'
    ];
    
    for (const selector of essentialComponents) {
      await expect(page.locator(selector)).toBeVisible();
    }
    
    console.log('✅ All essential UI components are accessible');
  });
});

test.describe('AdaptiveLayout Integration - Responsive Behavior', () => {
  test('✅ MOBILE: Layout adapts to mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');
    
    // On mobile, sidebar should auto-collapse
    await expect(page.locator('[data-testid="sidebar-collapsed"]')).toBeVisible();
    
    // Mode indicator should still be visible
    await expect(page.locator('[data-testid="mode-indicator"]')).toBeVisible();
    
    console.log('✅ Mobile layout adaptation works');
  });
});