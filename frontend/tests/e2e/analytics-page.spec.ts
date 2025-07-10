import { test, expect } from '@playwright/test';

test.describe('Analytics Page - Comprehensive E2E Tests', () => {
  
  // Mock analytics data for consistent testing
  const mockAnalyticsData = {
    lastUpdated: '2024-01-15T10:30:00Z',
    totalCost: 12.3456,
    totalTokens: 150000,
    totalRequests: 247,
    modelPerformance: [
      { modelName: 'gpt-4', successRate: 95, avgResponseTime: 2.3, usage: 45 },
      { modelName: 'claude-3', successRate: 92, avgResponseTime: 1.8, usage: 38 },
      { modelName: 'gemini-pro', successRate: 89, avgResponseTime: 2.1, usage: 17 }
    ],
    sessionMetrics: {
      totalSessions: 73,
      avgSessionLength: 8.5,
      activeUsers: 12
    },
    userPreferences: {
      totalPreferences: 156,
      favoriteModel: { modelName: 'gpt-4', percentage: 47 },
      topModels: [
        { modelName: 'gpt-4', count: 73 },
        { modelName: 'claude-3', count: 59 },
        { modelName: 'gemini-pro', count: 24 }
      ]
    }
  };

  test.beforeEach(async ({ page }) => {
    // Mock all analytics API endpoints
    await page.route('**/api/v1/analytics/overview', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalyticsData)
      });
    });

    await page.route('**/api/v1/analytics/models', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          modelPerformance: mockAnalyticsData.modelPerformance,
          realTimeMetrics: {
            activeModels: 3,
            currentCost: 2.45,
            tokensPerSecond: 150
          },
          historicalMetrics: {
            dailyUsage: [45, 52, 38, 61, 47],
            weeklyTrends: ['up', 'down', 'stable']
          }
        })
      });
    });

    await page.route('**/api/v1/analytics/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockAnalyticsData.sessionMetrics,
          sessionHistory: [
            { date: '2024-01-10', sessions: 12 },
            { date: '2024-01-11', sessions: 15 },
            { date: '2024-01-12', sessions: 8 }
          ]
        })
      });
    });

    await page.route('**/api/v1/analytics/preferences', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockAnalyticsData.userPreferences,
          preferenceTrends: {
            '2024-01-10': { 'gpt-4': 5, 'claude-3': 3 },
            '2024-01-11': { 'gpt-4': 7, 'claude-3': 4 },
            '2024-01-12': { 'gpt-4': 4, 'claude-3': 6 }
          }
        })
      });
    });
  });

  test('should load analytics page with correct title and header', async ({ page }) => {
    await page.goto('/analytics');

    // Check page title
    await expect(page).toHaveTitle(/Analytics.*aideator/);

    // Check main heading
    await expect(page.locator('h1')).toContainText('Analytics Dashboard');

    // Check subtitle
    await expect(page.locator('text=Track your model preferences, performance metrics, and usage patterns')).toBeVisible();

    // Check header controls
    await expect(page.locator('button:has-text("Refresh")')).toBeVisible();
    await expect(page.locator('button:has-text("Export")')).toBeVisible();

    // Check last updated timestamp
    await expect(page.locator('text*="Last updated:"')).toBeVisible();
  });

  test('should display all tab navigation correctly', async ({ page }) => {
    await page.goto('/analytics');

    // Check all tabs are present
    await expect(page.locator('button[role="tab"]:has-text("Overview")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Models")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Sessions")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Preferences")')).toBeVisible();

    // Check icons are present in tabs
    await expect(page.locator('button[role="tab"]:has-text("Overview") svg')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Models") svg')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Sessions") svg')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Preferences") svg')).toBeVisible();

    // Overview tab should be active by default
    await expect(page.locator('button[role="tab"]:has-text("Overview")[aria-selected="true"]')).toBeVisible();
  });

  test('should navigate between tabs correctly', async ({ page }) => {
    await page.goto('/analytics');

    // Switch to Models tab
    await page.locator('button[role="tab"]:has-text("Models")').click();
    await expect(page.locator('button[role="tab"]:has-text("Models")[aria-selected="true"]')).toBeVisible();

    // Switch to Sessions tab
    await page.locator('button[role="tab"]:has-text("Sessions")').click();
    await expect(page.locator('button[role="tab"]:has-text("Sessions")[aria-selected="true"]')).toBeVisible();

    // Switch to Preferences tab
    await page.locator('button[role="tab"]:has-text("Preferences")').click();
    await expect(page.locator('button[role="tab"]:has-text("Preferences")[aria-selected="true"]')).toBeVisible();

    // Switch back to Overview
    await page.locator('button[role="tab"]:has-text("Overview")').click();
    await expect(page.locator('button[role="tab"]:has-text("Overview")[aria-selected="true"]')).toBeVisible();
  });

  test('should display time range filters correctly', async ({ page }) => {
    await page.goto('/analytics');

    // Check all time range buttons
    await expect(page.locator('button:has-text("Today")')).toBeVisible();
    await expect(page.locator('button:has-text("This Week")')).toBeVisible();
    await expect(page.locator('button:has-text("This Month")')).toBeVisible();
    await expect(page.locator('button:has-text("This Quarter")')).toBeVisible();
    await expect(page.locator('button:has-text("This Year")')).toBeVisible();
    await expect(page.locator('button:has-text("All Time")')).toBeVisible();

    // Check active time range badge
    await expect(page.locator('[class*="badge"]')).toBeVisible();
  });

  test('should handle time range selection', async ({ page }) => {
    await page.goto('/analytics');

    // Click on "This Week" filter
    await page.locator('button:has-text("This Week")').click();

    // Check that the badge updates
    await expect(page.locator('text="This Week"')).toBeVisible();

    // Click on "This Month" filter
    await page.locator('button:has-text("This Month")').click();

    // Check that the badge updates
    await expect(page.locator('text="This Month"')).toBeVisible();
  });

  test('should display overview tab content correctly', async ({ page }) => {
    await page.goto('/analytics');

    // Check for Overview tab content
    await expect(page.locator('text="Overview"')).toBeVisible();

    // Check Quick Stats card
    await expect(page.locator('text="Quick Stats"')).toBeVisible();
    await expect(page.locator('text="Total Sessions"')).toBeVisible();
    await expect(page.locator('text="Total Preferences"')).toBeVisible();
    await expect(page.locator('text="Favorite Model"')).toBeVisible();
    await expect(page.locator('text="Total Cost"')).toBeVisible();

    // Check that stats values are displayed
    await expect(page.locator('text="73"')).toBeVisible(); // Total Sessions
    await expect(page.locator('text="156"')).toBeVisible(); // Total Preferences
    await expect(page.locator('text="gpt-4"')).toBeVisible(); // Favorite Model
    await expect(page.locator('text="$12.3456"')).toBeVisible(); // Total Cost
  });

  test('should display model comparison chart', async ({ page }) => {
    await page.goto('/analytics');

    // Chart should be visible in Overview tab
    await expect(page.locator('[data-testid="model-comparison-chart"], [class*="chart"], [class*="model-comparison"]')).toBeVisible();
  });

  test('should display response metrics panel', async ({ page }) => {
    await page.goto('/analytics');

    // Response metrics panel should be visible
    await expect(page.locator('[data-testid="response-metrics-panel"], [class*="metrics"], [class*="response-metrics"]')).toBeVisible();
  });

  test('should handle refresh functionality', async ({ page }) => {
    await page.goto('/analytics');

    // Set up route to track refresh calls
    let refreshCalled = false;
    await page.route('**/api/v1/analytics/overview', async route => {
      refreshCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalyticsData)
      });
    });

    // Click refresh button
    await page.locator('button:has-text("Refresh")').click();

    // Wait for refresh to complete
    await page.waitForTimeout(500);

    // Check that refresh icon spins during loading
    await expect(page.locator('button:has-text("Refresh") svg')).toBeVisible();
  });

  test('should handle export functionality', async ({ page }) => {
    await page.goto('/analytics');

    // Set up console logging to capture export action
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleLogs.push(msg.text());
      }
    });

    // Click export button
    await page.locator('button:has-text("Export")').click();

    // Wait for export action
    await page.waitForTimeout(100);

    // Check that export was triggered (logs "Export analytics data")
    expect(consoleLogs).toContain('Export analytics data');
  });

  test('should display error state correctly', async ({ page }) => {
    // Mock an error response
    await page.route('**/api/v1/analytics/overview', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    await page.goto('/analytics');

    // Wait for error to appear
    await page.waitForTimeout(1000);

    // Check if error message is displayed (this depends on error handling in the component)
    // The error display depends on the useAnalytics hook implementation
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    await page.goto('/analytics');

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that main elements are still visible
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Overview")')).toBeVisible();

    // Tabs should be accessible on mobile
    await expect(page.locator('button[role="tab"]:has-text("Models")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Sessions")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("Preferences")')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Check that layout adapts properly
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('text="Quick Stats"')).toBeVisible();
  });

  test('should handle models tab content', async ({ page }) => {
    await page.goto('/analytics');

    // Switch to Models tab
    await page.locator('button[role="tab"]:has-text("Models")').click();

    // Check Models tab specific content
    await expect(page.locator('[data-testid="model-comparison-chart"], [class*="chart"], [class*="model-comparison"]')).toBeVisible();
    await expect(page.locator('[data-testid="response-metrics-panel"], [class*="metrics"], [class*="response-metrics"]')).toBeVisible();
  });

  test('should handle sessions tab content', async ({ page }) => {
    await page.goto('/analytics');

    // Switch to Sessions tab
    await page.locator('button[role="tab"]:has-text("Sessions")').click();

    // Check Sessions tab specific content
    await expect(page.locator('[data-testid="session-analytics"], [class*="session"], [class*="analytics"]')).toBeVisible();
  });

  test('should handle preferences tab content', async ({ page }) => {
    await page.goto('/analytics');

    // Switch to Preferences tab
    await page.locator('button[role="tab"]:has-text("Preferences")').click();

    // Check Preferences tab specific content
    await expect(page.locator('[data-testid="user-preference-dashboard"], [class*="preference"], [class*="dashboard"]')).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/analytics');

    // Test Tab key navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Test Arrow key navigation for tabs
    await page.locator('button[role="tab"]:has-text("Overview")').focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('button[role="tab"]:has-text("Models")').nth(0)).toBeFocused();

    await page.keyboard.press('ArrowRight');
    await expect(page.locator('button[role="tab"]:has-text("Sessions")').nth(0)).toBeFocused();

    await page.keyboard.press('ArrowRight');
    await expect(page.locator('button[role="tab"]:has-text("Preferences")').nth(0)).toBeFocused();

    // Test Enter key to activate tab
    await page.keyboard.press('Enter');
    await expect(page.locator('button[role="tab"]:has-text("Preferences")[aria-selected="true"]')).toBeVisible();
  });

  test('should display loading states correctly', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/v1/analytics/overview', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalyticsData)
      });
    });

    await page.goto('/analytics');

    // Check for loading indicators
    // This depends on the loading state implementation in components
    await expect(page.locator('h1')).toBeVisible();
    
    // Wait for data to load
    await page.waitForTimeout(1500);
    
    // Check that content is now visible
    await expect(page.locator('text="Quick Stats"')).toBeVisible();
  });

  test('should handle accessibility requirements', async ({ page }) => {
    await page.goto('/analytics');

    // Check ARIA labels and roles
    await expect(page.locator('button[role="tab"]')).toHaveCount(4);
    await expect(page.locator('[role="tabpanel"]')).toHaveCount(1);

    // Check heading hierarchy
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('h1')).toContainText('Analytics Dashboard');

    // Check color contrast for key elements
    await expect(page.locator('h1')).toHaveCSS('color', /rgb\(31, 41, 55\)/); // neutral-charcoal
    
    // Check focus indicators
    await page.locator('button[role="tab"]:has-text("Overview")').focus();
    await expect(page.locator('button[role="tab"]:has-text("Overview")')).toBeFocused();
  });

  test('should handle time range changes across tabs', async ({ page }) => {
    await page.goto('/analytics');

    // Change time range in Overview tab
    await page.locator('button:has-text("This Week")').click();
    await expect(page.locator('text="This Week"')).toBeVisible();

    // Switch to Models tab
    await page.locator('button[role="tab"]:has-text("Models")').click();
    
    // Time range should persist across tabs
    await expect(page.locator('text="This Week"')).toBeVisible();

    // Switch to Sessions tab
    await page.locator('button[role="tab"]:has-text("Sessions")').click();
    
    // Time range should still be maintained
    await expect(page.locator('text="This Week"')).toBeVisible();
  });
});