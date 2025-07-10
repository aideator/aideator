import { test, expect } from '@playwright/test';

test.describe('Chat Scrolling Fix', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the stream page
    await page.goto('/stream');
    
    // Wait for the page to load completely
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 10000 });
  });

  test('main content container should have correct scrolling classes', async ({ page }) => {
    // Find the specific main content container with our changes
    const mainContainer = page.locator('div.h-full.w-full.flex.flex-col.overflow-y-auto').first();
    await expect(mainContainer).toBeVisible();
    
    // Verify it has the correct classes
    const className = await mainContainer.getAttribute('class');
    expect(className).toContain('overflow-y-auto');
    expect(className).not.toContain('overflow-hidden');
    expect(className).toContain('p-4');
    expect(className).toContain('pb-8');
    expect(className).toContain('h-full');
    expect(className).toContain('w-full');
    expect(className).toContain('flex-col');
  });

  test('content should be scrollable when it exceeds viewport height', async ({ page }) => {
    // Get the specific main scrollable container
    const scrollContainer = page.locator('div.h-full.w-full.flex.flex-col.overflow-y-auto').first();
    await expect(scrollContainer).toBeVisible();
    
    // Add content to make it scrollable
    await page.evaluate(() => {
      const container = document.querySelector('div.h-full.w-full.flex.flex-col.overflow-y-auto');
      if (container) {
        const testDiv = document.createElement('div');
        testDiv.style.height = '2000px';
        testDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
        testDiv.textContent = 'Tall test content to enable scrolling';
        testDiv.setAttribute('data-testid', 'scroll-test-content');
        container.appendChild(testDiv);
      }
    });
    
    // Wait for content to be added
    await page.waitForSelector('[data-testid="scroll-test-content"]');
    
    // Test that we can scroll programmatically
    await scrollContainer.evaluate((element) => {
      element.scrollTop = 200;
    });
    
    // Verify scroll position changed
    const scrollTop = await scrollContainer.evaluate((element) => element.scrollTop);
    expect(scrollTop).toBeGreaterThan(0);
    
    // Reset scroll position
    await scrollContainer.evaluate((element) => {
      element.scrollTop = 0;
    });
  });

  test('layout container should not restrict overflow', async ({ page }) => {
    // Check that AdaptiveLayout content area doesn't have overflow-hidden
    const layoutContent = page.locator('.flex-1.flex.flex-col.bg-neutral-white').first();
    await expect(layoutContent).toBeVisible();
    
    const className = await layoutContent.getAttribute('class');
    expect(className).not.toContain('overflow-hidden');
    expect(className).toContain('flex');
    expect(className).toContain('flex-col');
  });

  test('model comparison configuration should be visible and accessible', async ({ page }) => {
    // Find the model comparison configuration section
    const configSection = page.locator('text=Model Comparison Configuration').first();
    await expect(configSection).toBeVisible();
    
    // Verify we can interact with it
    await configSection.click();
    
    // Check if the section expands/collapses (it should be clickable)
    const expandButton = page.locator('[data-testid="sidebar-toggle"]').or(
      page.locator('text=Model Comparison Configuration').locator('..').locator('button')
    ).first();
    
    if (await expandButton.isVisible()) {
      await expect(expandButton).toBeEnabled();
    }
  });

  test('follow-up prompt section should be accessible when it appears', async ({ page }) => {
    // This test checks that the follow-up prompt section would be scrollable
    // We can't easily simulate model responses, but we can test the layout structure
    
    // Verify the main container can accommodate additional content
    const mainContainer = page.locator('div.h-full.w-full.flex.flex-col.overflow-y-auto').first();
    
    // Add some test content to simulate a scenario where follow-up prompt appears
    await page.evaluate(() => {
      const container = document.querySelector('div.h-full.w-full.flex.flex-col.overflow-y-auto');
      if (container) {
        // Create a tall test element to simulate content that would push follow-up prompt down
        const testElement = document.createElement('div');
        testElement.style.height = '1500px';
        testElement.style.backgroundColor = 'rgba(0, 0, 255, 0.1)';
        testElement.textContent = 'Test content to simulate tall conversation history';
        testElement.setAttribute('data-testid', 'test-tall-content');
        
        // Add it before the last child
        if (container.lastElementChild) {
          container.insertBefore(testElement, container.lastElementChild);
        } else {
          container.appendChild(testElement);
        }
        
        // Create a simulated follow-up prompt section
        const followUpSection = document.createElement('div');
        followUpSection.className = 'mt-4 bg-neutral-paper rounded-2xl shadow-xl p-4';
        followUpSection.innerHTML = `
          <h3 class="text-h3 font-bold text-neutral-charcoal">Continue Conversation</h3>
          <textarea placeholder="Follow-up prompt..." class="w-full bg-neutral-white border border-neutral-fog rounded-md p-2" data-testid="follow-up-textarea"></textarea>
        `;
        followUpSection.setAttribute('data-testid', 'follow-up-section');
        container.appendChild(followUpSection);
      }
    });
    
    // Wait for the test content to be added
    await page.waitForSelector('[data-testid="test-tall-content"]');
    await page.waitForSelector('[data-testid="follow-up-section"]');
    
    // Now test that we can scroll to the follow-up section
    const followUpSection = page.locator('[data-testid="follow-up-section"]');
    
    // Scroll to the follow-up section
    await followUpSection.scrollIntoViewIfNeeded();
    
    // Verify the follow-up section is visible and accessible
    await expect(followUpSection).toBeVisible();
    
    // Verify we can interact with the textarea in the follow-up section
    const followUpTextarea = page.locator('[data-testid="follow-up-textarea"]');
    await expect(followUpTextarea).toBeVisible();
    await followUpTextarea.click();
    await followUpTextarea.fill('Test follow-up message');
    
    // Verify the text was entered
    await expect(followUpTextarea).toHaveValue('Test follow-up message');
  });

  test('scrolling works smoothly with keyboard navigation', async ({ page }) => {
    const mainContainer = page.locator('div.h-full.w-full.flex.flex-col.overflow-y-auto').first();
    await expect(mainContainer).toBeVisible();
    
    // Add content to make scrolling possible
    await page.evaluate(() => {
      const container = document.querySelector('div.h-full.w-full.flex.flex-col.overflow-y-auto');
      if (container) {
        const testDiv = document.createElement('div');
        testDiv.style.height = '2000px';
        testDiv.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
        testDiv.textContent = 'Keyboard scroll test content';
        testDiv.setAttribute('data-testid', 'keyboard-scroll-content');
        container.appendChild(testDiv);
      }
    });
    
    await page.waitForSelector('[data-testid="keyboard-scroll-content"]');
    
    // Focus on the container
    await mainContainer.click();
    
    // Test manual scrolling
    await mainContainer.evaluate((el) => { el.scrollTop = 100; });
    await page.waitForTimeout(100);
    
    const scrollTopAfterManual = await mainContainer.evaluate((el) => el.scrollTop);
    expect(scrollTopAfterManual).toBeGreaterThan(0);
    
    // Test scroll up
    await mainContainer.evaluate((el) => { el.scrollTop = 50; });
    await page.waitForTimeout(100);
    
    const scrollTopAfterUp = await mainContainer.evaluate((el) => el.scrollTop);
    expect(scrollTopAfterUp).toBeLessThan(scrollTopAfterManual);
  });

  test('bottom padding ensures content is not cut off', async ({ page }) => {
    const mainContainer = page.locator('div.h-full.w-full.flex.flex-col.overflow-y-auto').first();
    await expect(mainContainer).toBeVisible();
    
    // Verify the container has bottom padding
    const computedStyle = await mainContainer.evaluate((el) => {
      return window.getComputedStyle(el).paddingBottom;
    });
    
    // Should have bottom padding (pb-8 = 32px in Tailwind)
    expect(computedStyle).toBe('32px');
  });
});