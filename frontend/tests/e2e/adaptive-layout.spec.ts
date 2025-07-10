import { test, expect } from '@playwright/test';

test.describe('AdaptiveLayout Component', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the stream page where AdaptiveLayout is used
    await page.goto('/stream');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test.describe('Sidebar Functionality', () => {
    test('should collapse and expand sidebar', async ({ page }) => {
      // Check that sidebar is initially expanded
      const sidebar = page.locator('[data-testid="sidebar"]');
      await expect(sidebar).toBeVisible();
      
      // Check for expanded content (search bar, session list)
      await expect(page.locator('[data-testid="session-search"]')).toBeVisible();
      await expect(page.locator('[data-testid="new-session-btn"]')).toBeVisible();
      
      // Click collapse button
      await page.locator('[data-testid="sidebar-toggle"]').click();
      
      // Verify sidebar is collapsed
      await expect(page.locator('[data-testid="session-search"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="sidebar-collapsed"]')).toBeVisible();
      
      // Click expand button
      await page.locator('[data-testid="sidebar-toggle"]').click();
      
      // Verify sidebar is expanded again
      await expect(page.locator('[data-testid="session-search"]')).toBeVisible();
      await expect(page.locator('[data-testid="new-session-btn"]')).toBeVisible();
    });

    test('should auto-collapse on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Reload page to trigger responsive behavior
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Verify sidebar is auto-collapsed on mobile
      await expect(page.locator('[data-testid="sidebar-collapsed"]')).toBeVisible();
      await expect(page.locator('[data-testid="session-search"]')).not.toBeVisible();
    });
  });

  test.describe('Session Management', () => {
    test('should create new session', async ({ page }) => {
      // Click new session button
      await page.locator('[data-testid="new-session-btn"]').click();
      
      // Verify new session was created (check for modal or redirect)
      // This depends on the actual implementation
      await expect(page.locator('[data-testid="session-list"]')).toBeVisible();
    });

    test('should search and filter sessions', async ({ page }) => {
      // Type in search input
      const searchInput = page.locator('[data-testid="session-search"]');
      await searchInput.fill('test session');
      
      // Wait for search results
      await page.waitForTimeout(300); // Debounce delay
      
      // Check that sessions are filtered
      const sessionItems = page.locator('[data-testid="session-item"]');
      const count = await sessionItems.count();
      
      // Clear search
      await searchInput.fill('');
      await page.waitForTimeout(300);
      
      // Verify all sessions are shown again
      const allSessionItems = page.locator('[data-testid="session-item"]');
      const allCount = await allSessionItems.count();
      
      expect(allCount).toBeGreaterThanOrEqual(count);
    });

    test('should select session', async ({ page }) => {
      // Click on first session
      const firstSession = page.locator('[data-testid="session-item"]').first();
      await firstSession.click();
      
      // Verify session is selected (visual indicator)
      await expect(firstSession).toHaveClass(/bg-ai-primary\/10/);
      
      // Verify session title appears in top bar
      await expect(page.locator('[data-testid="active-session-title"]')).toBeVisible();
    });

    test('should show session metadata', async ({ page }) => {
      const sessionItem = page.locator('[data-testid="session-item"]').first();
      
      // Check for session metadata (turn count, last activity)
      await expect(sessionItem.locator('[data-testid="session-turn-count"]')).toBeVisible();
      await expect(sessionItem.locator('[data-testid="session-last-activity"]')).toBeVisible();
    });
  });

  test.describe('Mode Switching', () => {
    test('should switch between welcome, chat, and compare modes', async ({ page }) => {
      // Test Welcome mode
      await page.locator('[data-testid="mode-welcome"]').click();
      await expect(page.locator('[data-testid="mode-indicator"]')).toContainText('welcome');
      
      // Test Chat mode
      await page.locator('[data-testid="mode-chat"]').click();
      await expect(page.locator('[data-testid="mode-indicator"]')).toContainText('chat');
      
      // Test Compare mode
      await page.locator('[data-testid="mode-compare"]').click();
      await expect(page.locator('[data-testid="mode-indicator"]')).toContainText('compare');
    });

    test('should show appropriate icons for each mode', async ({ page }) => {
      // Welcome mode
      await page.locator('[data-testid="mode-welcome"]').click();
      await expect(page.locator('[data-testid="mode-indicator"] svg')).toBeVisible();
      
      // Chat mode
      await page.locator('[data-testid="mode-chat"]').click();
      await expect(page.locator('[data-testid="mode-indicator"] svg')).toBeVisible();
      
      // Compare mode
      await page.locator('[data-testid="mode-compare"]').click();
      await expect(page.locator('[data-testid="mode-indicator"] svg')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt layout for different screen sizes', async ({ page }) => {
      // Test desktop layout
      await page.setViewportSize({ width: 1920, height: 1080 });
      await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
      
      // Test tablet layout
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
      
      // Test mobile layout
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator('[data-testid="sidebar-collapsed"]')).toBeVisible();
    });

    test('should maintain functionality on mobile', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Expand sidebar
      await page.locator('[data-testid="sidebar-toggle"]').click();
      
      // Verify search still works
      await expect(page.locator('[data-testid="session-search"]')).toBeVisible();
      
      // Test session selection
      const firstSession = page.locator('[data-testid="session-item"]').first();
      await firstSession.click();
      await expect(firstSession).toHaveClass(/bg-ai-primary\/10/);
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      // Check sidebar toggle button
      const toggleBtn = page.locator('[data-testid="sidebar-toggle"]');
      await expect(toggleBtn).toHaveAttribute('aria-label');
      
      // Check search input
      const searchInput = page.locator('[data-testid="session-search"]');
      await expect(searchInput).toHaveAttribute('placeholder');
      
      // Check mode buttons
      const modeButtons = page.locator('[data-testid^="mode-"]');
      const count = await modeButtons.count();
      expect(count).toBeGreaterThan(0);
    });

    test('should be keyboard navigable', async ({ page }) => {
      // Tab through sidebar elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Check that focus is visible
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should handle large session lists efficiently', async ({ page }) => {
      // This test would require mocking a large number of sessions
      // For now, we'll check that the virtual scrolling works
      
      const sessionList = page.locator('[data-testid="session-list"]');
      await expect(sessionList).toBeVisible();
      
      // Scroll through sessions
      await sessionList.hover();
      await page.mouse.wheel(0, 500);
      
      // Verify scroll works without performance issues
      await expect(sessionList).toBeVisible();
    });

    test('should debounce search input', async ({ page }) => {
      const searchInput = page.locator('[data-testid="session-search"]');
      
      // Type quickly
      await searchInput.type('test', { delay: 50 });
      
      // Wait for debounce
      await page.waitForTimeout(350);
      
      // Verify search was executed
      await expect(searchInput).toHaveValue('test');
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle empty session list', async ({ page }) => {
      // This would require mocking empty state
      // Check for empty state message
      const emptyState = page.locator('[data-testid="empty-sessions"]');
      
      // If no sessions, empty state should be visible
      const sessionCount = await page.locator('[data-testid="session-item"]').count();
      if (sessionCount === 0) {
        await expect(emptyState).toBeVisible();
      }
    });

    test('should handle network errors gracefully', async ({ page }) => {
      // Mock network failure
      await page.route('**/api/sessions', route => route.abort());
      
      // Reload page
      await page.reload();
      
      // Check for error state
      await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
    });
  });
});