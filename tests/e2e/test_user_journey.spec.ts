import { test, expect } from '@playwright/test';

test.describe('End-to-End User Journey Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock all API endpoints
    await page.route('**/api/v1/health', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy' })
      });
    });

    await page.route('**/api/v1/sessions', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'session-123',
            title: 'New Session',
            created_at: new Date().toISOString()
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      }
    });

    await page.route('**/api/v1/prompts', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          prompt_id: 'prompt-456',
          session_id: 'session-123',
          stream_url: 'http://localhost:8000/api/v1/prompts/prompt-456/stream',
          status: 'started',
          models: ['gpt-4', 'claude-3-opus', 'gemini-pro'],
          estimated_duration_seconds: 30
        })
      });
    });

    await page.route('**/api/v1/prompts/*/stream', async (route) => {
      const events = [
        'event: model_output\ndata: {"model_id": "gpt-4", "content": "Hello from GPT-4!", "type": "model_output"}\n\n',
        'event: model_output\ndata: {"model_id": "claude-3-opus", "content": "Hello from Claude!", "type": "model_output"}\n\n',
        'event: model_output\ndata: {"model_id": "gemini-pro", "content": "Hello from Gemini!", "type": "model_output"}\n\n',
        'event: model_complete\ndata: {"model_id": "gpt-4", "type": "model_complete", "response_time_ms": 2500, "token_count": 100}\n\n',
        'event: model_complete\ndata: {"model_id": "claude-3-opus", "type": "model_complete", "response_time_ms": 3000, "token_count": 120}\n\n',
        'event: model_complete\ndata: {"model_id": "gemini-pro", "type": "model_complete", "response_time_ms": 2800, "token_count": 110}\n\n',
        'event: comparison_complete\ndata: {"type": "comparison_complete"}\n\n'
      ];

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type'
        },
        body: events.join('')
      });
    });

    await page.route('**/api/v1/preferences', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });
  });

  test('complete user journey: session creation → prompt comparison → model selection', async ({ page }) => {
    // Navigate to application
    await page.goto('/stream');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify initial state
    await expect(page.locator('h1')).toContainText('aideator');
    await expect(page.locator('text=Multi-Model Prompt Comparison Platform')).toBeVisible();

    // Step 1: Configure comparison
    await expect(page.locator('text=Model Comparison Configuration')).toBeVisible();
    
    // Enter a prompt
    const promptInput = page.locator('textarea[placeholder*="Enter your prompt"]');
    await promptInput.fill('Write a short poem about artificial intelligence');

    // Verify character count updates
    await expect(page.locator('text=65 characters')).toBeVisible();

    // Select models (some should be pre-selected)
    await expect(page.locator('text=3 models selected')).toBeVisible();

    // Step 2: Start comparison
    const startButton = page.locator('button:has-text("Start Comparison")');
    await expect(startButton).toBeEnabled();
    await startButton.click();

    // Verify configuration panel collapses
    await expect(page.locator('text=3 models · Write a short poem about artificial intelligence...')).toBeVisible();

    // Step 3: Watch streaming responses
    await page.waitForTimeout(500); // Allow streaming to start

    // Verify model response panels appear
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude-3 Opus')).toBeVisible();
    await expect(page.locator('text=Gemini Pro')).toBeVisible();

    // Verify streaming indicators
    await expect(page.locator('text=Streaming').first()).toBeVisible();

    // Wait for responses to complete
    await page.waitForTimeout(2000);

    // Verify completion indicators
    await expect(page.locator('text=Done').first()).toBeVisible();

    // Verify response content appears
    await expect(page.locator('text=Hello from GPT-4!')).toBeVisible();
    await expect(page.locator('text=Hello from Claude!')).toBeVisible();
    await expect(page.locator('text=Hello from Gemini!')).toBeVisible();

    // Verify metrics display
    await expect(page.locator('text=2.5s')).toBeVisible(); // Response time
    await expect(page.locator('text=100 tokens')).toBeVisible(); // Token count

    // Step 4: Select preferred model
    const preferenceButton = page.locator('button:has-text("I prefer this")').first();
    await preferenceButton.click();

    // Verify selection feedback
    await expect(page.locator('button:has-text("Selected")')).toBeVisible();

    // Step 5: Stop comparison
    const stopButton = page.locator('button:has-text("Stop Comparison")');
    await stopButton.click();

    // Verify comparison stopped
    await expect(page.locator('text=Streaming')).not.toBeVisible();
    await expect(page.locator('button:has-text("Start Comparison")')).toBeVisible();
  });

  test('responsive design: mobile layout adaptation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Verify mobile layout
    await expect(page.locator('h1')).toContainText('aideator');
    
    // Configure and start comparison
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill('Test prompt');
    await page.locator('button:has-text("Start Comparison")').click();
    
    await page.waitForTimeout(1000);
    
    // Verify single-column layout on mobile
    const responseCards = page.locator('[data-testid="model-response-card"]');
    if (await responseCards.count() > 0) {
      // Check that cards stack vertically (grid-cols-1)
      const firstCard = responseCards.first();
      const secondCard = responseCards.nth(1);
      
      if (await secondCard.isVisible()) {
        const firstCardBox = await firstCard.boundingBox();
        const secondCardBox = await secondCard.boundingBox();
        
        // Cards should be stacked vertically (second card below first)
        expect(secondCardBox!.y).toBeGreaterThan(firstCardBox!.y + firstCardBox!.height);
      }
    }
  });

  test('error handling: network failures and recovery', async ({ page }) => {
    // Mock network failure
    await page.route('**/api/v1/prompts', async (route) => {
      await route.abort('failed');
    });

    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Try to start comparison
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill('Test prompt');
    await page.locator('button:has-text("Start Comparison")').click();

    // Verify error handling
    await expect(page.locator('text=Cannot connect to backend')).toBeVisible();

    // Restore network and try again
    await page.route('**/api/v1/prompts', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          prompt_id: 'prompt-456',
          session_id: 'session-123',
          stream_url: 'http://localhost:8000/api/v1/prompts/prompt-456/stream',
          status: 'started',
          models: ['gpt-4'],
          estimated_duration_seconds: 30
        })
      });
    });

    await page.locator('button:has-text("Start Comparison")').click();
    
    // Verify recovery
    await expect(page.locator('text=GPT-4')).toBeVisible();
  });

  test('accessibility: keyboard navigation and screen reader support', async ({ page }) => {
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Test keyboard navigation
    await page.keyboard.press('Tab'); // Should focus first interactive element
    await page.keyboard.press('Tab'); // Move to next element
    
    // Test prompt input accessibility
    const promptInput = page.locator('textarea[placeholder*="Enter your prompt"]');
    await promptInput.focus();
    await expect(promptInput).toBeFocused();
    
    // Test model selection accessibility
    await page.keyboard.press('Tab');
    const firstModelCheckbox = page.locator('input[type="checkbox"]').first();
    await expect(firstModelCheckbox).toBeFocused();
    
    // Test button accessibility
    await page.keyboard.press('Tab');
    const startButton = page.locator('button:has-text("Start Comparison")');
    await expect(startButton).toBeFocused();
    
    // Test Enter key activation
    await page.keyboard.press('Enter');
    // Should start comparison
    
    // Verify ARIA labels and roles
    await expect(page.locator('button[aria-label*="Start"]')).toBeVisible();
    await expect(page.locator('[role="button"]')).toHaveCount(1); // At least one button
  });

  test('performance: streaming with multiple models', async ({ page }) => {
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Start performance measurement
    const startTime = Date.now();

    // Configure for maximum models
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill('Performance test prompt');
    
    // Select all available models
    const modelCheckboxes = page.locator('input[type="checkbox"]');
    const modelCount = await modelCheckboxes.count();
    
    for (let i = 0; i < modelCount; i++) {
      await modelCheckboxes.nth(i).check();
    }

    // Start comparison
    await page.locator('button:has-text("Start Comparison")').click();

    // Wait for streaming to complete
    await page.waitForTimeout(3000);

    // Verify all models responded
    await expect(page.locator('text=Done')).toHaveCount(modelCount);

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Performance assertion (should complete within reasonable time)
    expect(duration).toBeLessThan(10000); // Less than 10 seconds
  });

  test('data persistence: session and preference storage', async ({ page }) => {
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Create comparison
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill('Persistence test');
    await page.locator('button:has-text("Start Comparison")').click();

    await page.waitForTimeout(2000);

    // Select a preference
    await page.locator('button:has-text("I prefer this")').first().click();

    // Verify local storage
    const sessionStorage = await page.evaluate(() => {
      return {
        currentSession: localStorage.getItem('aideator_current_session'),
        sessionCache: localStorage.getItem('aideator_session_cache')
      };
    });

    expect(sessionStorage.currentSession).toBeTruthy();
    expect(sessionStorage.sessionCache).toBeTruthy();

    // Reload page and verify persistence
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify session was restored
    const restoredStorage = await page.evaluate(() => {
      return {
        currentSession: localStorage.getItem('aideator_current_session'),
        sessionCache: localStorage.getItem('aideator_session_cache')
      };
    });

    expect(restoredStorage.currentSession).toBe(sessionStorage.currentSession);
    expect(restoredStorage.sessionCache).toBe(sessionStorage.sessionCache);
  });

  test('edge cases: empty prompts and model selection', async ({ page }) => {
    await page.goto('/stream');
    await page.waitForLoadState('networkidle');

    // Test empty prompt
    await page.locator('button:has-text("Start Comparison")').click();
    await expect(page.locator('text=Please enter a prompt')).toBeVisible();

    // Test with prompt but no models
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill('Test prompt');
    
    // Uncheck all models
    const modelCheckboxes = page.locator('input[type="checkbox"]');
    const modelCount = await modelCheckboxes.count();
    
    for (let i = 0; i < modelCount; i++) {
      await modelCheckboxes.nth(i).uncheck();
    }

    await page.locator('button:has-text("Start Comparison")').click();
    await expect(page.locator('text=Please select at least one model')).toBeVisible();

    // Test very long prompt
    const longPrompt = 'A'.repeat(10000);
    await page.locator('textarea[placeholder*="Enter your prompt"]').fill(longPrompt);
    await expect(page.locator('text=10000 characters')).toBeVisible();
  });

  test('concurrent users: multiple browser tabs simulation', async ({ context }) => {
    // Create multiple tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Navigate both tabs
    await page1.goto('/stream');
    await page2.goto('/stream');

    await page1.waitForLoadState('networkidle');
    await page2.waitForLoadState('networkidle');

    // Start comparisons in both tabs
    await page1.locator('textarea[placeholder*="Enter your prompt"]').fill('Tab 1 prompt');
    await page2.locator('textarea[placeholder*="Enter your prompt"]').fill('Tab 2 prompt');

    await page1.locator('button:has-text("Start Comparison")').click();
    await page2.locator('button:has-text("Start Comparison")').click();

    // Verify both work independently
    await expect(page1.locator('text=Tab 1 prompt')).toBeVisible();
    await expect(page2.locator('text=Tab 2 prompt')).toBeVisible();

    // Verify streaming in both
    await page1.waitForTimeout(2000);
    await page2.waitForTimeout(2000);

    await expect(page1.locator('text=Done')).toBeVisible();
    await expect(page2.locator('text=Done')).toBeVisible();
  });
});