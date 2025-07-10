import { test, expect } from '@playwright/test';

test.describe('Stream Page - React Hooks Order', () => {
  test('should render without hooks order errors during loading state', async ({ page }) => {
    // Capture any console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to stream page
    await page.goto('/stream');

    // Wait for the page to load (past the loading state)
    await page.waitForSelector('text=Model Comparison Configuration', { timeout: 10000 });

    // Check for React hooks errors
    const hooksErrors = consoleErrors.filter(error => 
      error.includes('order of Hooks') || 
      error.includes('Rules of Hooks') ||
      error.includes('Previous render') ||
      error.includes('Next render')
    );

    // Assert no hooks errors occurred
    expect(hooksErrors).toHaveLength(0);
  });

  test('should maintain consistent hooks order across re-renders', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/stream');
    
    // Wait for initial load
    await page.waitForSelector('text=Model Comparison Configuration');

    // Trigger re-renders by interacting with the page
    // Toggle the configuration panel
    await page.click('text=Model Comparison Configuration');
    await page.waitForTimeout(100);
    await page.click('text=Model Comparison Configuration');
    
    // Change mode if available
    const modeSelector = page.locator('text=Select Mode');
    if (await modeSelector.isVisible()) {
      await modeSelector.click();
    }

    // Check for hooks errors after interactions
    const hooksErrors = consoleErrors.filter(error => 
      error.includes('order of Hooks') || 
      error.includes('Rules of Hooks')
    );

    expect(hooksErrors).toHaveLength(0);
  });

  test('should handle auth loading state without breaking hooks', async ({ page }) => {
    // Slow down the auth loading to ensure we catch the loading state
    await page.route('**/api/v1/auth/**', route => {
      setTimeout(() => route.continue(), 1000);
    });

    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/stream');

    // Should show loading state
    await expect(page.locator('text=Authenticating...')).toBeVisible();

    // Wait for loading to complete
    await page.waitForSelector('text=Model Comparison Configuration', { timeout: 15000 });

    // No hooks errors should have occurred
    const hooksErrors = consoleErrors.filter(error => 
      error.includes('order of Hooks') || 
      error.includes('Rules of Hooks')
    );

    expect(hooksErrors).toHaveLength(0);
  });

  test('should render all UI elements after loading', async ({ page }) => {
    await page.goto('/stream');

    // Wait for main content to load
    await page.waitForSelector('text=Model Comparison Configuration');

    // Verify key elements are present
    await expect(page.locator('text=Model Comparison Configuration')).toBeVisible();
    
    // Check for prompt textarea
    const promptTextarea = page.locator('textarea[placeholder*="Enter your"]');
    await expect(promptTextarea).toBeVisible();

    // Check for start button
    const startButton = page.locator('button:has-text("Start Comparison")');
    await expect(startButton).toBeVisible();

    // Verify no loading spinner is shown
    await expect(page.locator('text=Authenticating...')).not.toBeVisible();
  });
});