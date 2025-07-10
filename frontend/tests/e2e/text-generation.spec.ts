import { test, expect } from '@playwright/test';

test.describe('Text Generation Behavior', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the streaming page
    await page.goto('/stream');
  });

  test('should not have choppy/shaky text during generation', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');

    // Fill in the GitHub URL (using default)
    const githubInput = page.locator('input[placeholder*="GitHub"]');
    await githubInput.fill('https://github.com/octocat/Hello-World');

    // Fill in the prompt
    const promptInput = page.locator('textarea[placeholder*="prompt"]');
    await promptInput.fill('Analyze this repository');

    // Click the generate button
    const generateButton = page.locator('button', { hasText: 'Generate' });
    await generateButton.click();

    // Wait for streaming to start
    await page.waitForSelector('[data-testid="stream-card"]', { timeout: 10000 });

    // Get the first stream card
    const streamCard = page.locator('[data-testid="stream-card"]').first();
    
    // Take screenshots to analyze text rendering
    await page.screenshot({ path: 'test-results/before-streaming.png' });
    
    // Wait for some text to appear
    await page.waitForFunction(() => {
      const cards = document.querySelectorAll('[data-testid="stream-card"]');
      return Array.from(cards).some(card => {
        const content = card.textContent;
        return content && content.length > 50; // Some meaningful content
      });
    }, { timeout: 30000 });

    // Take screenshot during streaming
    await page.screenshot({ path: 'test-results/during-streaming.png' });

    // Monitor for layout shifts during streaming
    let layoutShifts = 0;
    page.on('console', msg => {
      if (msg.text().includes('Layout shift')) {
        layoutShifts++;
      }
    });

    // Add script to monitor layout shifts
    await page.addInitScript(() => {
      // Monitor for layout shifts
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.hadRecentInput) continue;
          console.log('Layout shift:', entry.value);
        }
      });
      observer.observe({ entryTypes: ['layout-shift'] });
    });

    // Wait for streaming to progress
    await page.waitForTimeout(5000);

    // Check if text is being rendered smoothly
    const streamContent = await streamCard.locator('.stream-content').textContent();
    expect(streamContent).toBeTruthy();
    
    // Verify the stream card is stable (not jumping around)
    const initialBounds = await streamCard.boundingBox();
    
    // Wait a bit more and check bounds again
    await page.waitForTimeout(2000);
    const finalBounds = await streamCard.boundingBox();
    
    // The card should not have moved significantly
    if (initialBounds && finalBounds) {
      const xDiff = Math.abs(initialBounds.x - finalBounds.x);
      const yDiff = Math.abs(initialBounds.y - finalBounds.y);
      
      expect(xDiff).toBeLessThan(5); // Allow minor variations
      expect(yDiff).toBeLessThan(5);
    }

    // Take final screenshot
    await page.screenshot({ path: 'test-results/after-streaming.png' });

    // Stop streaming
    const stopButton = page.locator('button', { hasText: 'Stop' });
    if (await stopButton.isVisible()) {
      await stopButton.click();
    }
  });

  test('should have smooth text rendering without visual glitches', async ({ page }) => {
    // Navigate to stream page
    await page.goto('/stream');

    // Start a generation with default settings
    const generateButton = page.locator('button', { hasText: 'Generate' });
    await generateButton.click();

    // Wait for streaming to start
    await page.waitForSelector('[data-testid="stream-card"]', { timeout: 10000 });

    // Monitor for rapid DOM changes that could cause choppiness
    let domChanges = 0;
    const observer = await page.evaluateHandle(() => {
      const targetNode = document.querySelector('[data-testid="stream-card"]');
      if (!targetNode) return null;

      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' || mutation.type === 'characterData') {
            window.domChangeCount = (window.domChangeCount || 0) + 1;
          }
        });
      });

      observer.observe(targetNode, {
        childList: true,
        subtree: true,
        characterData: true
      });

      return observer;
    });

    // Wait for some streaming
    await page.waitForTimeout(3000);

    // Check DOM change frequency
    const changeCount = await page.evaluate(() => window.domChangeCount || 0);
    
    // Should have changes (streaming is working) but not excessive
    expect(changeCount).toBeGreaterThan(0);
    expect(changeCount).toBeLessThan(1000); // Not too many rapid changes

    // Clean up
    await observer.dispose();
  });
});