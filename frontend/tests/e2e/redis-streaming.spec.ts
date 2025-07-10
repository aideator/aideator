import { test, expect } from '@playwright/test';

test.describe('Redis Streaming', () => {
  test.beforeEach(async ({ page }) => {
    // Start each test on the stream page
    await page.goto('/stream');
    
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
  });

  test('should use Redis streaming when selected', async ({ page }) => {
    // Wait for the form to be visible
    await page.waitForSelector('select', { state: 'visible' });
    
    // Find and click the settings button (it's the second button with SVG)
    const settingsButton = page.locator('button.ml-2.p-1\\.5.text-gray-400');
    await settingsButton.click();
    
    // Wait for popover to be visible
    await page.waitForSelector('#streaming-backend-switch', { state: 'visible' });
    
    // Toggle to Redis
    await page.click('#streaming-backend-switch');
    
    // Verify localStorage was updated
    const backend = await page.evaluate(() => localStorage.getItem('streamingBackend'));
    expect(backend).toBe('redis');
    
    // Close popover by clicking outside
    await page.keyboard.press('Escape');
    
    // Fill in the form
    await page.fill('textarea[placeholder*="Describe what you want"]', 'Test prompt for Redis streaming');
    
    // Set up request interception before clicking start
    const streamRequestPromise = page.waitForRequest(req => 
      req.url().includes('/stream/redis'),
      { timeout: 10000 }
    );
    
    // Start a run
    await page.click('button:has-text("Start Generation")');
    
    // Verify it calls the Redis endpoint
    const request = await streamRequestPromise;
    expect(request.url()).toContain('/api/v1/runs/');
    expect(request.url()).toContain('/stream/redis');
  });

  test('should persist streaming backend preference', async ({ page }) => {
    // Wait for form to be visible
    await page.waitForSelector('select', { state: 'visible' });
    
    // Open settings and toggle to Redis
    const settingsButton = page.locator('button.ml-2.p-1\\.5.text-gray-400');
    await settingsButton.click();
    await page.waitForSelector('#streaming-backend-switch', { state: 'visible' });
    await page.click('#streaming-backend-switch');
    
    // Close popover
    await page.keyboard.press('Escape');
    
    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Wait for form to be visible again
    await page.waitForSelector('select', { state: 'visible' });
    
    // Open settings again
    await settingsButton.click();
    await page.waitForSelector('#streaming-backend-switch', { state: 'visible' });
    
    // Verify the switch is still on (Redis)
    const isChecked = await page.isChecked('#streaming-backend-switch');
    expect(isChecked).toBe(true);
    
    // Verify localStorage
    const backend = await page.evaluate(() => localStorage.getItem('streamingBackend'));
    expect(backend).toBe('redis');
  });

  test('should use kubectl streaming when deselected', async ({ page }) => {
    // First set to Redis
    await page.evaluate(() => localStorage.setItem('streamingBackend', 'redis'));
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Wait for form
    await page.waitForSelector('select', { state: 'visible' });
    
    // Open settings and toggle back to kubectl
    const settingsButton = page.locator('button.ml-2.p-1\\.5.text-gray-400');
    await settingsButton.click();
    await page.waitForSelector('#streaming-backend-switch', { state: 'visible' });
    await page.click('#streaming-backend-switch');
    
    // Close popover
    await page.keyboard.press('Escape');
    
    // Fill form
    await page.fill('textarea[placeholder*="Describe what you want"]', 'Test prompt for kubectl streaming');
    
    // Set up request interception
    const streamRequestPromise = page.waitForRequest(req => 
      req.url().includes('/stream') && !req.url().includes('/redis'),
      { timeout: 10000 }
    );
    
    // Start a run
    await page.click('button:has-text("Start Generation")');
    
    // Verify it calls the kubectl endpoint (not redis)
    const request = await streamRequestPromise;
    expect(request.url()).toContain('/api/v1/runs/');
    expect(request.url()).toMatch(/\/stream$/); // Ends with /stream, not /stream/redis
  });

  test('should show correct status text for each backend', async ({ page }) => {
    // Wait for form
    await page.waitForSelector('select', { state: 'visible' });
    
    // Open settings
    const settingsButton = page.locator('button.ml-2.p-1\\.5.text-gray-400');
    await settingsButton.click();
    await page.waitForSelector('#streaming-backend-switch', { state: 'visible' });
    
    // Check kubectl status text
    await expect(page.locator('text=Kubectl logs streaming (default)')).toBeVisible();
    
    // Toggle to Redis
    await page.click('#streaming-backend-switch');
    
    // Check Redis status text
    await expect(page.locator('text=Redis pub/sub for improved reliability')).toBeVisible();
  });
});