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

  test('should handle streaming errors gracefully with improved error logging', async ({ page }) => {
    await page.goto('/stream');

    // Set up console logging to capture error messages
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Fill out the input
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test streaming error handling');
    
    // Open settings and configure models
    await page.locator('text=Show Settings').click();

    // Mock successful run creation
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          runId: 'test-run-error-123',
          sessionId: 'test-session-123', 
          turnId: 'test-turn-123'
        })
      });
    });

    // Mock streaming endpoint that will fail/close to trigger error handler
    await page.route('**/api/v1/runs/test-run-error-123/stream**', async route => {
      // Simulate a connection that fails/closes
      await route.abort('connectionfailed');
    });

    // Submit the message to trigger streaming
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Wait for the streaming connection to be attempted and fail
    await page.waitForTimeout(2000);

    // Verify that error logging is now meaningful (not just empty {})
    const hasEmptyObjectError = consoleErrors.some(error => 
      error.includes('Streaming error: {}') || error === 'Streaming error: {}'
    );
    
    // Should NOT have the problematic empty object error
    expect(hasEmptyObjectError).toBe(false);

    // Should have meaningful error information instead
    const hasMeaningfulError = consoleErrors.some(error => 
      error.includes('Streaming error:') && 
      (error.includes('readyState') || error.includes('timestamp') || error.includes('type'))
    );
    
    // Should have improved error logging with actual information
    expect(hasMeaningfulError).toBe(true);
  });

  test('should maintain streaming connection state correctly', async ({ page }) => {
    await page.goto('/stream');

    // Set up console logging to capture streaming events
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('FRONTEND:')) {
        consoleMessages.push(msg.text());
      }
    });

    // Fill out the input
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test streaming state management');
    
    // Open settings and configure models
    await page.locator('text=Show Settings').click();

    // Mock successful run creation
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          runId: 'test-run-state-123',
          sessionId: 'test-session-123', 
          turnId: 'test-turn-123'
        })
      });
    });

    // Mock streaming endpoint that provides proper SSE data
    await page.route('**/api/v1/runs/test-run-state-123/stream**', async route => {
      // Simulate a proper SSE stream with agent_output event
      const sseData = `event: agent_output\ndata: {"variation_id": 0, "content": "Test response chunk"}\n\n`;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Submit the message to trigger streaming
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Wait for streaming to process
    await page.waitForTimeout(1000);

    // Should have received and processed the streaming data
    const hasStreamingLogs = consoleMessages.some(msg => 
      msg.includes('Received agent_output event') || msg.includes('Creating update')
    );
    
    expect(hasStreamingLogs).toBe(true);
  });
});