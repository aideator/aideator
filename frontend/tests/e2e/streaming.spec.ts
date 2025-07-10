import { test, expect } from '@playwright/test';

test.describe('aideator Streaming Interface', () => {
  test('should load streaming page with ChatGPT-style layout', async ({ page }) => {
    await page.goto('/stream');

    // Check welcome message (when no conversation)
    await expect(page.locator('h1')).toContainText('aideator');
    await expect(page.locator('text=Multi-Model Prompt Comparison Platform')).toBeVisible();

    // Check bottom input area is visible
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    
    // Check settings toggle button
    await expect(page.locator('text=Show Settings')).toBeVisible();

    // Check send button is present
    await expect(page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play')).toBeVisible();
  });

  test('should validate input and enable send button', async ({ page }) => {
    await page.goto('/stream');

    // Send button should be disabled with empty input
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await expect(sendButton).toBeDisabled();

    // Type in input area
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test prompt for analysis');

    // Open settings to configure models (needed for validation)
    await page.locator('text=Show Settings').click();
    
    // Button should now be enabled with valid input
    await expect(sendButton).toBeEnabled();
  });

  test('should display model configuration in settings', async ({ page }) => {
    await page.goto('/stream');

    // Open settings panel
    await page.locator('text=Show Settings').click();

    // Check that model configuration is available
    await expect(page.locator('text=Select Models')).toBeVisible();

    // Check that mode selector is present
    await expect(page.locator('[data-testid="mode-selector"], text*="Mode"')).toBeVisible();

    // Should show model count in quick info
    await expect(page.locator('text*="models"')).toBeVisible();
  });

  test('should display welcome state initially', async ({ page }) => {
    await page.goto('/stream');

    // Should show welcome message when no conversation
    await expect(page.locator('h1')).toContainText('aideator');
    await expect(page.locator('text=Multi-Model Prompt Comparison Platform')).toBeVisible();

    // Input should be ready for first message
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeEmpty();
  });

  test('should handle message submission (mock test)', async ({ page }) => {
    await page.goto('/stream');

    // Fill out the input
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Analyze this repository structure');
    
    // Open settings and configure models
    await page.locator('text=Show Settings').click();

    // Mock the API call to avoid needing backend
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          runId: 'test-run-123',
          sessionId: 'test-session-123', 
          turnId: 'test-turn-123'
        })
      });
    });

    // Submit the message
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Should show the user message in conversation
    await expect(page.locator('text=Analyze this repository structure')).toBeVisible();
  });

  test('should be responsive with ChatGPT-style layout', async ({ page }) => {
    await page.goto('/stream');

    // Desktop view - should show full layout
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    await expect(page.locator('h1')).toContainText('aideator');

    // Mobile view - should still be functional
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    await expect(page.locator('text=Show Settings')).toBeVisible();

    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    await expect(page.locator('h1')).toContainText('aideator');
  });

  test('should display authentication status', async ({ page }) => {
    await page.goto('/stream');

    // Should show auth status in top right
    await expect(page.locator('[class*="fixed"][class*="top-4"][class*="right-4"]')).toBeVisible();

    // Settings should show authentication info when expanded
    await page.locator('text=Show Settings').click();
    // Auth debug info or connection status should be visible in development mode
  });

  test('should have proper design system styling', async ({ page }) => {
    await page.goto('/stream');

    // Check AI primary color usage (welcome section)
    await expect(page.locator('[class*="bg-gradient-to-br"][class*="from-ai-primary"]')).toBeVisible();

    // Check neutral paper background (input area)
    const inputCard = page.locator('[class*="bg-neutral-paper"]').first();
    await expect(inputCard).toBeVisible();

    // Check proper spacing and typography
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();
    
    // Check bottom fixed input area
    await expect(page.locator('[class*="fixed"][class*="bottom-0"]')).toBeVisible();
  });

  test('should support keyboard shortcuts', async ({ page }) => {
    await page.goto('/stream');

    // Focus on input area
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.click();
    await promptInput.fill('Test message');

    // Test Enter key submission (without Shift)
    await promptInput.press('Enter');
    
    // Should have submitted the message (input should be cleared or message should appear)
    // This tests the onKeyDown handler in the textarea
  });

  test('should display conversation history correctly', async ({ page }) => {
    await page.goto('/stream');

    // This test would need to simulate a conversation with responses
    // For now, just test that the conversation area exists
    await expect(page.locator('[class*="flex-1"][class*="overflow-y-auto"]')).toBeVisible();
    
    // Welcome message should be in conversation area when empty
    await expect(page.locator('h1')).toContainText('aideator');
  });
});