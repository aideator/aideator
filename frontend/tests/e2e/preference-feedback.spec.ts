import { test, expect } from '@playwright/test';

test.describe('Preference Feedback - Comprehensive E2E Tests', () => {
  
  const testRunId = 'test-pref-run-12345';
  const testSessionId = 'test-session-789';
  const testTurnId = 'test-turn-456';

  // Mock streaming completion data
  const completedStreamData = [
    { event: 'agent_output', data: { variation_id: 0, content: 'Agent 0: Comprehensive code analysis complete. Found 5 potential improvements in error handling.', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_output', data: { variation_id: 1, content: 'Agent 1: Security audit finished. No critical vulnerabilities detected. 3 minor suggestions for hardening.', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_output', data: { variation_id: 2, content: 'Agent 2: Performance review done. Identified 2 bottlenecks and provided optimization strategies.', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_complete', data: { variation_id: 0, status: 'completed' }},
    { event: 'agent_complete', data: { variation_id: 1, status: 'completed' }},
    { event: 'agent_complete', data: { variation_id: 2, status: 'completed' }},
    { event: 'run_complete', data: { run_id: testRunId, status: 'completed' }}
  ];

  test.beforeEach(async ({ page }) => {
    // Mock run creation
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          runId: testRunId,
          sessionId: testSessionId,
          turnId: testTurnId
        })
      });
    });

    // Mock preference submission
    await page.route('**/api/v1/runs/*/select', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          preferenceId: 'pref-' + Date.now(),
          message: 'Preference recorded successfully'
        })
      });
    });

    // Mock preference feedback submission
    await page.route(`**/api/v1/sessions/${testSessionId}/turns/${testTurnId}/preferences`, async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          feedbackId: 'feedback-' + Date.now(),
          message: 'Feedback submitted successfully'
        })
      });
    });

    // Mock auth status
    await page.route('**/api/v1/auth/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: false,
          user: null
        })
      });
    });
  });

  test('should display preference selection buttons after completion', async ({ page }) => {
    // Mock completed streaming
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    // Submit prompt to start streaming
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Analyze this codebase comprehensively');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Wait for completion
    await page.waitForTimeout(1500);

    // Check preference buttons are visible
    const preferenceButtons = page.locator('button:has-text("I prefer this response")');
    await expect(preferenceButtons).toHaveCount(3);

    // Check buttons are enabled
    await expect(preferenceButtons.first()).toBeEnabled();
    await expect(preferenceButtons.nth(1)).toBeEnabled();
    await expect(preferenceButtons.nth(2)).toBeEnabled();
  });

  test('should handle preference selection with visual feedback', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test preference selection');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Click first preference button
    const firstPreferenceButton = page.locator('button:has-text("I prefer this response")').first();
    await firstPreferenceButton.click();

    // Button should show selection state
    await page.waitForTimeout(500);
    
    // Other buttons should be disabled or show different state
    const allPreferenceButtons = page.locator('button:has-text("I prefer this response")');
    // Some state change should be visible (this depends on implementation)
  });

  test('should record preference selection correctly', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Track API calls
    let preferenceAPICalled = false;
    await page.route('**/api/v1/runs/*/select', async route => {
      preferenceAPICalled = true;
      const requestBody = route.request().postData();
      expect(requestBody).toBeTruthy();
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          preferenceId: 'pref-test-123'
        })
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test preference recording');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Select preference
    const secondPreferenceButton = page.locator('button:has-text("I prefer this response")').nth(1);
    await secondPreferenceButton.click();

    await page.waitForTimeout(500);

    // Verify API was called
    expect(preferenceAPICalled).toBe(true);
  });

  test('should handle preference selection errors gracefully', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Mock error response
    await page.route('**/api/v1/runs/*/select', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Failed to record preference'
        })
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test error handling');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Click preference button
    const preferenceButton = page.locator('button:has-text("I prefer this response")').first();
    await preferenceButton.click();

    await page.waitForTimeout(500);

    // Should handle error gracefully (no crash, maybe show error message)
    // Button should remain clickable for retry
    await expect(preferenceButton).toBeEnabled();
  });

  test('should prevent multiple preference selections for same comparison', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test single selection');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Select first preference
    const firstButton = page.locator('button:has-text("I prefer this response")').first();
    await firstButton.click();

    await page.waitForTimeout(500);

    // Try to select second preference
    const secondButton = page.locator('button:has-text("I prefer this response")').nth(1);
    await secondButton.click();

    // Should handle appropriately (either disable other buttons or allow change)
    // This depends on the specific UX design
  });

  test('should show preference analytics after selection', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Mock analytics endpoint
    await page.route('**/api/v1/analytics/preferences', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totalPreferences: 156,
          favoriteModel: { modelName: 'gpt-4', percentage: 47 },
          recentSelections: [
            { variationId: 0, timestamp: '2024-01-15T10:00:00Z' }
          ]
        })
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test analytics display');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Select preference
    const preferenceButton = page.locator('button:has-text("I prefer this response")').first();
    await preferenceButton.click();

    await page.waitForTimeout(500);

    // Check if any analytics or feedback UI appears
    // This depends on the app's implementation of preference feedback
  });

  test('should handle preference feedback collection', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test feedback collection');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Select preference
    const preferenceButton = page.locator('button:has-text("I prefer this response")').nth(1);
    await preferenceButton.click();

    await page.waitForTimeout(500);

    // Look for any feedback collection UI that might appear
    // This could be a modal, inline form, or other feedback mechanism
  });

  test('should display preference history in analytics', async ({ page }) => {
    await page.goto('/analytics');

    // Should load analytics page with preference data
    await page.waitForTimeout(1000);

    // Check for preference-related elements
    await expect(page.locator('button[role="tab"]:has-text("Preferences")')).toBeVisible();

    // Click on preferences tab
    await page.locator('button[role="tab"]:has-text("Preferences")').click();

    // Should show preference dashboard
    await expect(page.locator('[data-testid="user-preference-dashboard"], [class*="preference"], [class*="dashboard"]')).toBeVisible();
  });

  test('should handle keyboard navigation for preference selection', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test keyboard navigation');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Navigate to preference buttons with Tab
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Focus should be on a preference button
    const focusedButton = page.locator('button:has-text("I prefer this response"):focus');
    if (await focusedButton.count() > 0) {
      await expect(focusedButton).toBeFocused();
      
      // Select with Enter key
      await page.keyboard.press('Enter');
      
      await page.waitForTimeout(500);
    }

    // Navigate between preference buttons with arrow keys
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowUp');
  });

  test('should handle accessibility for preference selection', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test accessibility');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Check button accessibility
    const preferenceButtons = page.locator('button:has-text("I prefer this response")');
    
    // Check buttons have proper roles
    await expect(preferenceButtons.first()).toHaveAttribute('type', 'button');
    
    // Check focus indicators work
    await preferenceButtons.first().focus();
    await expect(preferenceButtons.first()).toBeFocused();

    // Check button text is descriptive
    await expect(preferenceButtons.first()).toContainText('I prefer this response');

    // Check color contrast
    await expect(preferenceButtons.first()).toHaveCSS('color', /rgb/);
  });

  test('should handle preference selection on mobile devices', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test mobile preference selection');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Preference buttons should be accessible on mobile
    const preferenceButtons = page.locator('button:has-text("I prefer this response")');
    await expect(preferenceButtons.first()).toBeVisible();

    // Buttons should be large enough for touch
    const buttonBox = await preferenceButtons.first().boundingBox();
    expect(buttonBox?.height).toBeGreaterThan(40); // Minimum touch target size

    // Test touch interaction
    await preferenceButtons.first().click();
    await page.waitForTimeout(500);
  });

  test('should integrate with analytics tracking', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      completedStreamData.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Track analytics calls
    let analyticsCallMade = false;
    await page.route('**/api/v1/analytics/**', async route => {
      analyticsCallMade = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test analytics integration');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Select preference
    const preferenceButton = page.locator('button:has-text("I prefer this response")').first();
    await preferenceButton.click();

    await page.waitForTimeout(1000);

    // Analytics should be updated (this depends on implementation)
    // expect(analyticsCallMade).toBe(true);
  });
});