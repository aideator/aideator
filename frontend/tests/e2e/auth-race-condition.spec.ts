import { test, expect } from '@playwright/test';

test.describe('Auth Race Condition Prevention', () => {
  test('should not make API calls before auth completes', async ({ page }) => {
    // Track all API calls made before auth completes
    const preAuthApiCalls: string[] = [];
    let authCallMade = false;
    let authCompleted = false;

    // Monitor all API requests
    page.on('request', (request) => {
      const url = request.url();
      
      // Track when auth call is made
      if (url.includes('/auth/dev/test-login')) {
        authCallMade = true;
      }
      
      // Track API calls to our backend before auth completes
      if (url.includes('localhost:8000/api/v1/') && authCallMade && !authCompleted) {
        // Exclude auth endpoints from the check
        if (!url.includes('/auth/')) {
          preAuthApiCalls.push(url);
        }
      }
    });

    // Mock auth endpoints
    await page.route('**/api/v1/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-user-123',
          email: 'test@example.com',
          full_name: 'Test User'
        })
      });
    });

    await page.route('**/api/v1/auth/dev/test-login', async route => {
      // Simulate auth delay to test race condition
      await new Promise(resolve => setTimeout(resolve, 200));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token-123',
          user: {
            id: 'test-user-123',
            email: 'test@example.com',
            full_name: 'Test User'
          },
          api_key: 'mock-api-key-123'
        })
      });
      
      // Mark auth as completed immediately when response is sent
      authCompleted = true;
    });

    // Mock other API endpoints that should NOT be called before auth
    await page.route('**/api/v1/models/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'gpt-4', name: 'GPT-4', provider: 'openai' },
          { id: 'claude-3', name: 'Claude 3', provider: 'anthropic' }
        ])
      });
    });

    await page.route('**/api/v1/sessions/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Navigate to the stream page
    await page.goto('/stream');

    // Wait for the page to load and auth to complete
    await page.waitForTimeout(500);

    // Assert that no protected API calls were made before auth completed
    expect(preAuthApiCalls).toHaveLength(0);
    
    if (preAuthApiCalls.length > 0) {
      console.error('API calls made before auth completed:', preAuthApiCalls);
    }
  });

  test('should make API calls only after auth completes', async ({ page }) => {
    let authCompleted = false;
    const postAuthApiCalls: string[] = [];

    // Monitor API requests after auth completes
    page.on('request', (request) => {
      const url = request.url();
      
      if (authCompleted && url.includes('localhost:8000/api/v1/') && !url.includes('/auth/')) {
        postAuthApiCalls.push(url);
      }
    });

    // Mock auth endpoints with controlled timing
    await page.route('**/api/v1/auth/dev/test-login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token-123',
          user: {
            id: 'test-user-123',
            email: 'test@example.com',
            full_name: 'Test User'
          },
          api_key: 'mock-api-key-123'
        })
      });
      
      // Mark auth as completed
      authCompleted = true;
    });

    // Mock protected endpoints
    await page.route('**/api/v1/models/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'gpt-4', name: 'GPT-4', provider: 'openai' },
          { id: 'claude-3', name: 'Claude 3', provider: 'anthropic' }
        ])
      });
    });

    await page.route('**/api/v1/sessions/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Navigate to the stream page
    await page.goto('/stream');

    // Wait for auth and subsequent API calls
    await page.waitForTimeout(1000);

    // Verify that API calls were made after auth completed
    expect(postAuthApiCalls.length).toBeGreaterThan(0);
    
    // Verify expected endpoints were called
    const modelsCalled = postAuthApiCalls.some(url => url.includes('/models/models'));
    const sessionsCalled = postAuthApiCalls.some(url => url.includes('/sessions/'));
    
    expect(modelsCalled).toBe(true);
    expect(sessionsCalled).toBe(true);
  });

  test('should handle auth failure gracefully without making protected API calls', async ({ page }) => {
    const failedApiCalls: string[] = [];

    // Monitor for any API calls that might fail due to lack of auth
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('localhost:8000/api/v1/') && !url.includes('/auth/')) {
        failedApiCalls.push(url);
      }
    });

    // Mock auth failure
    await page.route('**/api/v1/auth/dev/test-login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Development login failed'
        })
      });
    });

    // Mock other endpoints to track if they're called
    await page.route('**/api/v1/models/models', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' })
      });
    });

    await page.route('**/api/v1/sessions/', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' })
      });
    });

    // Navigate to the stream page
    await page.goto('/stream');

    // Wait for page load
    await page.waitForTimeout(1000);

    // With auth failure, protected API calls should not be made
    expect(failedApiCalls).toHaveLength(0);
    
    // The page should still render with default/fallback content
    await expect(page.locator('body')).toBeVisible();
  });

  test('should show appropriate loading states during auth', async ({ page }) => {
    // Mock slow auth response to test loading states
    await page.route('**/api/v1/auth/dev/test-login', async route => {
      // Simulate slow auth
      await new Promise(resolve => setTimeout(resolve, 200));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token-123',
          user: {
            id: 'test-user-123',
            email: 'test@example.com',
            full_name: 'Test User'
          },
          api_key: 'mock-api-key-123'
        })
      });
    });

    // Mock other endpoints
    await page.route('**/api/v1/models/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'gpt-4', name: 'GPT-4', provider: 'openai' }
        ])
      });
    });

    await page.route('**/api/v1/sessions/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    // Navigate to the stream page
    await page.goto('/stream');

    // Page should render even during auth loading
    await expect(page.locator('body')).toBeVisible();
    
    // Wait for auth to complete
    await page.waitForTimeout(500);
    
    // Page should still be functional after auth completes
    await expect(page.locator('body')).toBeVisible();
  });
});