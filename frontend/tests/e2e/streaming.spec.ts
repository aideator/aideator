import { test, expect } from '@playwright/test';

test.describe('AIdeator Streaming Interface', () => {
  test('should load streaming page with configuration form', async ({ page }) => {
    await page.goto('/stream');

    // Check page elements
    await expect(page.locator('h1')).toContainText('AIdeator');
    await expect(page.locator('text=Generation Configuration')).toBeVisible();

    // Check form elements
    await expect(page.locator('label:has-text("GitHub Repository URL")')).toBeVisible();
    await expect(page.locator('label:has-text("Task Prompt")')).toBeVisible();
    await expect(page.locator('label:has-text("Agent Variations")')).toBeVisible();

    // Check default values
    const githubInput = page.locator('input[type="url"]');
    await expect(githubInput).toHaveValue('https://github.com/octocat/Hello-World');

    const promptTextarea = page.locator('textarea');
    await expect(promptTextarea).toHaveValue('Analyze this repository and suggest improvements.');
  });

  test('should validate form inputs', async ({ page }) => {
    await page.goto('/stream');

    // Clear required fields
    await page.locator('input[type="url"]').clear();
    await page.locator('textarea').clear();

    // Try to submit with empty fields
    const startButton = page.locator('text=Start Generation');
    await expect(startButton).toBeDisabled();

    // Fill in valid data
    await page.locator('input[type="url"]').fill('https://github.com/octocat/Hello-World');
    await page.locator('textarea').fill('Test prompt for analysis');

    // Button should now be enabled
    await expect(startButton).toBeEnabled();
  });

  test('should display agent variation selector', async ({ page }) => {
    await page.goto('/stream');

    // Check variation selector
    const variationSelect = page.locator('[data-placeholder]').filter({ hasText: /\d+ Agents?/ });
    await expect(variationSelect).toBeVisible();

    // Click to open dropdown
    await variationSelect.click();

    // Check options are available
    await expect(page.locator('text=1 Agent')).toBeVisible();
    await expect(page.locator('text=2 Agents')).toBeVisible();
    await expect(page.locator('text=3 Agents')).toBeVisible();
    await expect(page.locator('text=4 Agents')).toBeVisible();
    await expect(page.locator('text=5 Agents')).toBeVisible();

    // Select 5 agents
    await page.locator('text=5 Agents').click();
  });

  test('should display empty agent grid initially', async ({ page }) => {
    await page.goto('/stream');

    // Check that the streaming grid section exists
    await expect(page.locator('text=Agent Variations')).toBeVisible();
    await expect(page.locator('text=agents working in parallel')).toBeVisible();

    // Should show empty state
    await expect(page.locator('text=Ready to Start')).toBeVisible();
    await expect(page.locator('text=Configure your task')).toBeVisible();
  });

  test('should handle form submission (mock test)', async ({ page }) => {
    await page.goto('/stream');

    // Fill out the form
    await page.locator('input[type="url"]').fill('https://github.com/octocat/Hello-World');
    await page.locator('textarea').fill('Analyze this repository structure');
    
    // Select number of agents
    await page.locator('[data-placeholder]').filter({ hasText: /\d+ Agents?/ }).click();
    await page.locator('text=3 Agents').click();

    // Mock the API call to avoid needing backend
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          run_id: 'test-run-123',
          stream_url: '/api/v1/runs/test-run-123/stream',
          status: 'accepted'
        })
      });
    });

    // Submit the form
    await page.locator('text=Start Generation').click();

    // Should show that generation is starting
    await expect(page.locator('text=Stop Generation')).toBeVisible();
  });

  test('should be responsive with agent grid layout', async ({ page }) => {
    await page.goto('/stream');

    // Desktop view - should show grid layout
    await page.setViewportSize({ width: 1920, height: 1080 });
    const agentGrid = page.locator('[class*="grid"]').filter({ hasText: 'Agent Variations' });
    await expect(agentGrid).toBeVisible();

    // Mobile view - should still be functional
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('text=Generation Configuration')).toBeVisible();
    await expect(page.locator('input[type="url"]')).toBeVisible();

    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('text=Agent Variations')).toBeVisible();
  });

  test('should display connection status indicator', async ({ page }) => {
    await page.goto('/stream');

    // Should show disconnected status initially
    await expect(page.locator('text=Disconnected')).toBeVisible();

    // Connection status should be visible with icon
    const statusBadge = page.locator('[class*="border"]').filter({ hasText: 'Disconnected' });
    await expect(statusBadge).toBeVisible();
  });

  test('should have proper design system styling', async ({ page }) => {
    await page.goto('/stream');

    // Check AI primary color usage
    const primaryElements = page.locator('[class*="text-ai-primary"]');
    await expect(primaryElements.first()).toBeVisible();

    // Check neutral paper background
    const configCard = page.locator('[class*="bg-neutral-paper"]').first();
    await expect(configCard).toBeVisible();

    // Check proper spacing and typography
    const headings = page.locator('h1, h2, h3');
    await expect(headings.first()).toBeVisible();
  });

  test('should handle navigation back to homepage', async ({ page }) => {
    await page.goto('/stream');

    // Check that we can navigate back to homepage (via logo/header)
    const logo = page.locator('[class*="text-ai-primary"]').first();
    if (await logo.count() > 0) {
      // If there's a clickable logo, test navigation
      const isClickable = await logo.getAttribute('href') !== null || 
                         await logo.locator('..').getAttribute('href') !== null;
      
      if (isClickable) {
        await logo.click();
        await expect(page).toHaveURL('/');
      }
    }
  });
});