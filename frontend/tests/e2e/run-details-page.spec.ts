import { test, expect } from '@playwright/test';

test.describe('Run Details Page - Comprehensive E2E Tests', () => {
  
  const testRunId = 'test-run-12345';

  // Mock data for SSE events
  const mockAgentOutputs = [
    { variation_id: 0, content: 'Starting analysis of repository...', pod: 'agent-pod-0' },
    { variation_id: 1, content: 'Initializing code review process...', pod: 'agent-pod-1' },
    { variation_id: 0, content: 'Found 47 files in repository', pod: 'agent-pod-0' },
    { variation_id: 1, content: 'Analyzing code structure and patterns', pod: 'agent-pod-1' },
    { variation_id: 0, content: 'Analyzing main.py and requirements.txt', pod: 'agent-pod-0' },
    { variation_id: 1, content: 'Security scan completed - no issues found', pod: 'agent-pod-1' }
  ];

  const mockJobStatuses = [
    { variation_id: 0, status: 'completed', job_name: 'agent-test-run-12345-0' },
    { variation_id: 1, status: 'completed', job_name: 'agent-test-run-12345-1' }
  ];

  const mockRunStatus = {
    run_id: testRunId,
    status: 'completed',
    message: 'All agents completed successfully'
  };

  test.beforeEach(async ({ page }) => {
    // Mock the select winner API endpoint
    await page.route('**/api/v1/runs/*/select', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Winner selected successfully'
        })
      });
    });
  });

  test('should load run details page with correct title and navigation', async ({ page }) => {
    await page.goto(`/runs/${testRunId}`);

    // Check page elements
    await expect(page.locator(`text=Run: ${testRunId}`)).toBeVisible();
    
    // Check back button
    await expect(page.locator('text=Back to Home')).toBeVisible();
    await expect(page.locator('a[href="/"]')).toBeVisible();
    
    // Check back button has arrow icon
    await expect(page.locator('svg').first()).toBeVisible(); // ArrowLeft icon
  });

  test('should navigate back to home when back button is clicked', async ({ page }) => {
    await page.goto(`/runs/${testRunId}`);

    // Click back button
    await page.locator('text=Back to Home').click();

    // Should navigate to home page
    await expect(page).toHaveURL('/');
  });

  test('should display initial loading state', async ({ page }) => {
    await page.goto(`/runs/${testRunId}`);

    // Should show loading state when no outputs yet
    await expect(page.locator('text=Waiting for agent outputs...')).toBeVisible();
    await expect(page.locator('svg.animate-spin')).toBeVisible(); // Loading spinner
  });

  test('should handle SSE connection and display run status', async ({ page }) => {
    // Mock SSE endpoint with run status
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      const sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for SSE connection
    await page.waitForTimeout(500);

    // Check status badge
    await expect(page.locator('text=Completed')).toBeVisible();
    
    // Check connection indicator
    await expect(page.locator('text=Connected to stream')).toBeVisible();
    await expect(page.locator('.animate-ping')).toBeVisible(); // Connection pulse
  });

  test('should display agent outputs and tabs correctly', async ({ page }) => {
    // Mock SSE endpoint with agent outputs
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      // Add agent outputs
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });
      
      // Add job completion events
      mockJobStatuses.forEach(status => {
        sseData += `event: job_completed\ndata: ${JSON.stringify(status)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for outputs to load
    await page.waitForTimeout(1000);

    // Check tabs are created
    await expect(page.locator('button[role="tab"]:has-text("Variation 1")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Variation 2")')).toBeVisible();

    // Check completion icons in tabs
    await expect(page.locator('button[role="tab"]:has-text("Variation 1") svg')).toBeVisible(); // CheckCircle
    await expect(page.locator('button[role="tab"]:has-text("Variation 2") svg')).toBeVisible(); // CheckCircle

    // Check first variation is active by default
    await expect(page.locator('button[role="tab"]:has-text("Variation 1")[aria-selected="true"]')).toBeVisible();
  });

  test('should display agent output content correctly', async ({ page }) => {
    // Mock SSE endpoint with agent outputs
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      // Add specific agent outputs for variation 0
      const variation0Outputs = mockAgentOutputs.filter(output => output.variation_id === 0);
      variation0Outputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for outputs to load
    await page.waitForTimeout(1000);

    // Check output content is displayed
    await expect(page.locator('text=Starting analysis of repository...')).toBeVisible();
    await expect(page.locator('text=Found 47 files in repository')).toBeVisible();
    await expect(page.locator('text=Analyzing main.py and requirements.txt')).toBeVisible();

    // Check output is in pre-formatted block
    await expect(page.locator('pre').filter({ hasText: 'Starting analysis' })).toBeVisible();
  });

  test('should handle tab navigation between variations', async ({ page }) => {
    // Mock SSE endpoint with outputs for both variations
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for outputs to load
    await page.waitForTimeout(1000);

    // Should start on Variation 1
    await expect(page.locator('text=Starting analysis of repository...')).toBeVisible();

    // Click on Variation 2 tab
    await page.locator('button[role="tab"]:has-text("Variation 2")').click();

    // Should show Variation 2 content
    await expect(page.locator('text=Initializing code review process...')).toBeVisible();
    await expect(page.locator('text=Security scan completed - no issues found')).toBeVisible();

    // Switch back to Variation 1
    await page.locator('button[role="tab"]:has-text("Variation 1")').click();

    // Should show Variation 1 content again
    await expect(page.locator('text=Starting analysis of repository...')).toBeVisible();
  });

  test('should display select winner buttons when run is completed', async ({ page }) => {
    // Mock SSE endpoint with completed run
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      mockJobStatuses.forEach(status => {
        sseData += `event: job_completed\ndata: ${JSON.stringify(status)}\n\n`;
      });

      sseData += `event: run_complete\ndata: {}\n\n`;

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for completion
    await page.waitForTimeout(1000);

    // Check select winner button is visible
    await expect(page.locator('button:has-text("Select as Winner")')).toBeVisible();

    // Switch to second variation and check button there too
    await page.locator('button[role="tab"]:has-text("Variation 2")').click();
    await expect(page.locator('button:has-text("Select as Winner")')).toBeVisible();
  });

  test('should handle winner selection functionality', async ({ page }) => {
    // Mock SSE endpoint with completed run
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      mockJobStatuses.forEach(status => {
        sseData += `event: job_completed\ndata: ${JSON.stringify(status)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for completion
    await page.waitForTimeout(1000);

    // Click select winner button
    const selectButton = page.locator('button:has-text("Select as Winner")');
    await selectButton.click();

    // Should show loading state briefly, then success state
    await page.waitForTimeout(200);

    // Button should change to "Selected as Winner" with check icon
    await expect(page.locator('button:has-text("Selected as Winner")')).toBeVisible();
    await expect(page.locator('button:has-text("Selected as Winner") svg')).toBeVisible(); // CheckCircle icon
  });

  test('should handle agent errors correctly', async ({ page }) => {
    const errorData = {
      variation_id: 0,
      error: 'Connection timeout to LLM provider',
      job_name: 'agent-test-run-12345-0'
    };

    // Mock SSE endpoint with agent error
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify({ ...mockRunStatus, status: 'running' })}\n\n`;
      
      // Add some outputs then an error
      sseData += `event: agent_output\ndata: ${JSON.stringify(mockAgentOutputs[0])}\n\n`;
      sseData += `event: agent_error\ndata: ${JSON.stringify(errorData)}\n\n`;

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for error to appear
    await page.waitForTimeout(1000);

    // Check error alert is displayed
    await expect(page.locator('[role="alert"]')).toBeVisible();
    await expect(page.locator('text=Connection timeout to LLM provider')).toBeVisible();
    
    // Check error icon
    await expect(page.locator('[role="alert"] svg')).toBeVisible(); // AlertCircle icon
  });

  test('should display different status badges correctly', async ({ page }) => {
    const statusTests = [
      { status: 'starting', expectedText: 'Starting', expectedIcon: true },
      { status: 'running', expectedText: 'Running', expectedIcon: true },
      { status: 'completed', expectedText: 'Completed', expectedIcon: true },
      { status: 'failed', expectedText: 'Failed', expectedIcon: true },
      { status: 'cancelled', expectedText: 'Cancelled', expectedIcon: true }
    ];

    for (const statusTest of statusTests) {
      // Mock SSE endpoint with specific status
      await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
        const statusData = { ...mockRunStatus, status: statusTest.status };
        const sseData = `event: status\ndata: ${JSON.stringify(statusData)}\n\n`;
        
        await route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: sseData
        });
      });

      await page.goto(`/runs/${testRunId}`);
      await page.waitForTimeout(500);

      // Check status badge text
      await expect(page.locator(`text=${statusTest.expectedText}`)).toBeVisible();
      
      // Check status badge has icon
      if (statusTest.expectedIcon) {
        const statusBadge = page.locator(`text=${statusTest.expectedText}`).locator('..');
        await expect(statusBadge.locator('svg')).toBeVisible();
      }
    }
  });

  test('should handle connection loss gracefully', async ({ page }) => {
    // Mock SSE endpoint that closes connection
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      // Simulate connection error
      await route.abort('connectionfailed');
    });

    await page.goto(`/runs/${testRunId}`);

    // Wait for connection attempt
    await page.waitForTimeout(1000);

    // Should still show the loading state or handle gracefully
    await expect(page.locator('text=Waiting for agent outputs...')).toBeVisible();
    
    // Connection indicator should not show "Connected to stream"
    await expect(page.locator('text=Connected to stream')).not.toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Mock SSE endpoint with agent outputs
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/runs/${testRunId}`);

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Check that main elements are still visible and functional
    await expect(page.locator(`text=Run: ${testRunId}`)).toBeVisible();
    await expect(page.locator('text=Back to Home')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Variation 1")')).toBeVisible();

    // Check that tabs are scrollable/accessible on mobile
    await page.locator('button[role="tab"]:has-text("Variation 2")').click();
    await expect(page.locator('button[role="tab"]:has-text("Variation 2")[aria-selected="true"]')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator(`text=Run: ${testRunId}`)).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Mock SSE endpoint with agent outputs
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      mockJobStatuses.forEach(status => {
        sseData += `event: job_completed\ndata: ${JSON.stringify(status)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);
    await page.waitForTimeout(1000);

    // Test tab navigation with keyboard
    await page.locator('button[role="tab"]:has-text("Variation 1")').focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('button[role="tab"]:has-text("Variation 2")').nth(0)).toBeFocused();

    // Test Enter key to activate tab
    await page.keyboard.press('Enter');
    await expect(page.locator('button[role="tab"]:has-text("Variation 2")[aria-selected="true"]')).toBeVisible();

    // Test Tab key to navigate to select winner button
    await page.keyboard.press('Tab');
    await expect(page.locator('button:has-text("Select as Winner")')).toBeFocused();

    // Test Enter key to select winner
    await page.keyboard.press('Enter');
    await page.waitForTimeout(200);
    await expect(page.locator('button:has-text("Selected as Winner")')).toBeVisible();
  });

  test('should handle accessibility requirements', async ({ page }) => {
    // Mock SSE endpoint with agent outputs
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      
      mockAgentOutputs.forEach(output => {
        sseData += `event: agent_output\ndata: ${JSON.stringify(output)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);
    await page.waitForTimeout(1000);

    // Check ARIA labels and roles
    await expect(page.locator('button[role="tab"]')).toHaveCount(2);
    await expect(page.locator('[role="tabpanel"]')).toHaveCount(1);

    // Check heading hierarchy
    await expect(page.locator('h2')).toHaveCount(1);
    await expect(page.locator('h2')).toContainText(`Run: ${testRunId}`);

    // Check that buttons have proper ARIA attributes
    const backButton = page.locator('text=Back to Home');
    await expect(backButton).toBeVisible();

    // Check focus indicators work
    await page.locator('button[role="tab"]:has-text("Variation 1")').focus();
    await expect(page.locator('button[role="tab"]:has-text("Variation 1")')).toBeFocused();
  });

  test('should handle long outputs with proper scrolling', async ({ page }) => {
    // Create very long output content
    const longOutput = 'Line ' + Array.from({ length: 100 }, (_, i) => `Line ${i + 1}: This is a long line of output content to test scrolling behavior.`).join('\n');
    
    const longOutputEvent = {
      variation_id: 0,
      content: longOutput,
      pod: 'agent-pod-0'
    };

    // Mock SSE endpoint with long output
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify(mockRunStatus)}\n\n`;
      sseData += `event: agent_output\ndata: ${JSON.stringify(longOutputEvent)}\n\n`;

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);
    await page.waitForTimeout(1000);

    // Check that output container has proper max-height and overflow
    const outputContainer = page.locator('pre').first();
    await expect(outputContainer).toBeVisible();
    
    // Check that content is scrollable
    await expect(outputContainer).toContainText('Line 1:');
    
    // Test scrolling works by checking CSS properties
    const scrollHeight = await outputContainer.evaluate(el => el.scrollHeight);
    const clientHeight = await outputContainer.evaluate(el => el.clientHeight);
    
    // ScrollHeight should be greater than clientHeight for scrollable content
    expect(scrollHeight).toBeGreaterThan(clientHeight);
  });

  test('should handle multiple error types correctly', async ({ page }) => {
    const multipleErrors = [
      { variation_id: 0, error: 'Network timeout error', job_name: 'agent-test-run-12345-0' },
      { variation_id: 0, error: 'Authentication failed', job_name: 'agent-test-run-12345-0' },
      { variation_id: 1, error: 'Rate limit exceeded', job_name: 'agent-test-run-12345-1' }
    ];

    // Mock SSE endpoint with multiple errors
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = `event: status\ndata: ${JSON.stringify({ ...mockRunStatus, status: 'failed' })}\n\n`;
      
      multipleErrors.forEach(error => {
        sseData += `event: agent_error\ndata: ${JSON.stringify(error)}\n\n`;
      });

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto(`/runs/${testRunId}`);
    await page.waitForTimeout(1000);

    // Check multiple errors are displayed for variation 1
    await expect(page.locator('text=Network timeout error')).toBeVisible();
    await expect(page.locator('text=Authentication failed')).toBeVisible();

    // Switch to variation 2 and check its error
    await page.locator('button[role="tab"]:has-text("Variation 2")').click();
    await expect(page.locator('text=Rate limit exceeded')).toBeVisible();
  });
});