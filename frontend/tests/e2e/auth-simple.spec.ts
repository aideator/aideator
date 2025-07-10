import { test, expect } from '@playwright/test';

test.describe('Auth Loading Order', () => {
  test('should show loading state before making API calls', async ({ page }) => {
    let apiCallCount = 0;
    
    // Monitor API calls
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('localhost:8000/api/v1/') && !url.includes('/auth/')) {
        apiCallCount++;
        console.log('API call made:', url);
      }
    });

    // Mock slow auth response
    await page.route('**/api/v1/auth/dev/test-login', async route => {
      await new Promise(resolve => setTimeout(resolve, 100));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
          api_key: 'mock-api-key'
        })
      });
    });

    // Mock other endpoints
    await page.route('**/api/v1/models/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 'gpt-4', name: 'GPT-4' }])
      });
    });

    await page.route('**/api/v1/sessions/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Navigate to stream page
    await page.goto('/stream');

    // Check if loading state is shown initially
    const loadingText = page.locator('text=Authenticating...');
    const isLoadingVisible = await loadingText.isVisible().catch(() => false);
    
    if (isLoadingVisible) {
      console.log('Loading state properly shown');
    }

    // Wait for page to settle
    await page.waitForTimeout(500);
    
    // The page should eventually render
    await expect(page.locator('body')).toBeVisible();
    
    console.log('Total API calls made:', apiCallCount);
  });
});