import { test, expect } from '@playwright/test';

test.describe('Adaptive Layout Session List Padding', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mock sessions API
    await page.route('**/api/v1/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          sessions: [
            {
              id: 'session-1',
              title: 'Test Session 1',
              description: 'First test session',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              turnCount: 5,
              lastActivity: '5 minutes ago',
              isActive: true,
              isArchived: false,
            },
            {
              id: 'session-2',
              title: 'Test Session 2',
              description: 'Second test session',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              turnCount: 3,
              lastActivity: '1 hour ago',
              isActive: false,
              isArchived: false,
            },
            {
              id: 'session-3',
              title: 'Test Session 3',
              description: 'Third test session',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              turnCount: 8,
              lastActivity: '2 hours ago',
              isActive: false,
              isArchived: false,
            }
          ] 
        })
      });
    });

    // Mock auth endpoints to auto-login
    await page.route('**/api/v1/auth/auto-login-dev', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          token_type: 'bearer',
          user: {
            id: '123',
            email: 'test@example.com',
            is_active: true,
            created_at: new Date().toISOString()
          }
        })
      });
    });

    // Mock API key
    await page.route('**/api/v1/auth/api-keys', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{
          id: 'key-123',
          name: 'Test Key',
          key: 'ak-test-key',
          created_at: new Date().toISOString()
        }])
      });
    });

    // Navigate to stream page
    await page.goto('/stream');
    
    // Wait for the AdaptiveLayout to load
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 10000 });
  });

  test('should have proper padding for session list container', async ({ page }) => {
    // Ensure sidebar is expanded
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toBeVisible();
    
    // Check session list container
    const sessionList = page.locator('[data-testid="session-list"]');
    await expect(sessionList).toBeVisible();
    
    // Get the session items
    const sessionItems = page.locator('[data-testid="session-item"]');
    await expect(sessionItems).toHaveCount(3);
    
    // Check that sessions are not snapped to the top by verifying padding
    const sessionListBox = await sessionList.boundingBox();
    const firstSessionBox = await sessionItems.first().boundingBox();
    
    if (sessionListBox && firstSessionBox) {
      // The parent has px-2 (8px) padding, so sessions should not be right at the edge
      const horizontalPadding = firstSessionBox.x - sessionListBox.x;
      expect(horizontalPadding).toBeGreaterThanOrEqual(8); // px-2 = 8px
    }
    
    // Check spacing between sessions
    const secondSessionBox = await sessionItems.nth(1).boundingBox();
    if (firstSessionBox && secondSessionBox) {
      const spacing = secondSessionBox.y - (firstSessionBox.y + firstSessionBox.height);
      expect(spacing).toBeGreaterThanOrEqual(4); // space-y-1 = 4px
    }
  });

  test('should have proper layout when sidebar is collapsed', async ({ page }) => {
    // Toggle sidebar to collapsed state
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();
    
    // Wait for animation
    await page.waitForTimeout(400);
    
    // Check collapsed sidebar
    const collapsedSidebar = page.locator('[data-testid="sidebar-collapsed"]');
    await expect(collapsedSidebar).toBeVisible();
    
    // Check that collapsed buttons have proper padding
    const collapsedButtons = page.locator('[data-testid="session-item-collapsed"]');
    const firstButton = collapsedButtons.first();
    
    const sidebarBox = await collapsedSidebar.boundingBox();
    const buttonBox = await firstButton.boundingBox();
    
    if (sidebarBox && buttonBox) {
      // p-2 = 8px padding
      const padding = buttonBox.x - sidebarBox.x;
      expect(padding).toBeGreaterThanOrEqual(8);
    }
  });

  test('should display empty state with proper padding', async ({ page }) => {
    // Mock empty sessions
    await page.route('**/api/v1/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] })
      });
    });
    
    // Reload to get empty state
    await page.reload();
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 10000 });
    
    // Check empty state
    const emptyState = page.locator('[data-testid="empty-sessions"]');
    await expect(emptyState).toBeVisible();
    
    // Verify empty state has proper padding (py-8 = 32px vertical padding)
    const emptyStateBox = await emptyState.boundingBox();
    if (emptyStateBox) {
      expect(emptyStateBox.height).toBeGreaterThan(60); // Icon + text + padding
    }
  });

  test('should maintain proper spacing with search results', async ({ page }) => {
    // Search for a session
    const searchInput = page.locator('[data-testid="session-search"]');
    await searchInput.fill('Test Session 1');
    
    // Wait for filtering
    await page.waitForTimeout(100);
    
    // Should show only one session
    const sessionItems = page.locator('[data-testid="session-item"]');
    await expect(sessionItems).toHaveCount(1);
    
    // Check that the single result still has proper positioning
    const sessionList = page.locator('[data-testid="session-list"]');
    const sessionListBox = await sessionList.boundingBox();
    const sessionBox = await sessionItems.first().boundingBox();
    
    if (sessionListBox && sessionBox) {
      // Should still have horizontal padding
      const horizontalPadding = sessionBox.x - sessionListBox.x;
      expect(horizontalPadding).toBeGreaterThanOrEqual(8);
    }
  });

  test('should handle responsive padding on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Sidebar should auto-collapse on mobile
    await page.waitForTimeout(100);
    
    const collapsedSidebar = page.locator('[data-testid="sidebar-collapsed"]');
    await expect(collapsedSidebar).toBeVisible();
    
    // Toggle to expand on mobile
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();
    
    await page.waitForTimeout(400);
    
    // Check that expanded sidebar still has proper padding on mobile
    const sessionList = page.locator('[data-testid="session-list"]');
    const sessionItems = page.locator('[data-testid="session-item"]');
    
    const sessionListBox = await sessionList.boundingBox();
    const firstSessionBox = await sessionItems.first().boundingBox();
    
    if (sessionListBox && firstSessionBox) {
      // Should maintain padding even on mobile
      const horizontalPadding = firstSessionBox.x - sessionListBox.x;
      expect(horizontalPadding).toBeGreaterThanOrEqual(8);
    }
  });

  test('should verify visual hierarchy with proper spacing', async ({ page }) => {
    // Check the overall visual hierarchy
    const sidebar = page.locator('[data-testid="sidebar"]');
    const newSessionBtn = page.locator('[data-testid="new-session-btn"]');
    const searchInput = page.locator('[data-testid="session-search"]');
    const sessionList = page.locator('[data-testid="session-list"]');
    
    // All elements should be visible
    await expect(sidebar).toBeVisible();
    await expect(newSessionBtn).toBeVisible();
    await expect(searchInput).toBeVisible();
    await expect(sessionList).toBeVisible();
    
    // Verify vertical spacing between elements
    const btnBox = await newSessionBtn.boundingBox();
    const searchBox = await searchInput.boundingBox();
    const listBox = await sessionList.boundingBox();
    
    if (btnBox && searchBox) {
      // space-y-3 = 12px between button and search
      const btnToSearchSpacing = searchBox.y - (btnBox.y + btnBox.height);
      expect(btnToSearchSpacing).toBeGreaterThan(8);
    }
    
    if (searchBox && listBox) {
      // Should have spacing between search and list
      const searchToListSpacing = listBox.y - (searchBox.y + searchBox.height);
      expect(searchToListSpacing).toBeGreaterThan(0);
    }
  });
});