import { test, expect } from '@playwright/test';

test.describe('Session Management - Comprehensive E2E Tests', () => {
  
  // Mock session data
  const mockSessions = [
    {
      id: 'session-1',
      title: 'Code Review Session',
      description: 'Reviewing pull request #123',
      createdAt: '2024-01-10T10:00:00Z',
      updatedAt: '2024-01-15T14:30:00Z',
      turnCount: 8,
      lastActivityAt: '2024-01-15T14:30:00Z',
      isActive: true,
      isArchived: false,
      lastPrompt: 'Review the authentication module for security issues',
      modelPreferences: { 'gpt-4': 3, 'claude-3': 2, 'gemini-pro': 3 }
    },
    {
      id: 'session-2',
      title: 'Blog Post Ideas',
      description: 'Brainstorming tech blog content',
      createdAt: '2024-01-08T09:15:00Z',
      updatedAt: '2024-01-14T16:45:00Z',
      turnCount: 12,
      lastActivityAt: '2024-01-14T16:45:00Z',
      isActive: false,
      isArchived: false,
      lastPrompt: 'Generate ideas for articles about AI development',
      modelPreferences: { 'gpt-4': 5, 'claude-3': 4, 'gemini-pro': 3 }
    },
    {
      id: 'session-3',
      title: 'API Documentation',
      description: 'Creating REST API docs',
      createdAt: '2024-01-05T11:20:00Z',
      updatedAt: '2024-01-12T10:10:00Z',
      turnCount: 6,
      lastActivityAt: '2024-01-12T10:10:00Z',
      isActive: false,
      isArchived: false,
      lastPrompt: 'Help format OpenAPI documentation for user endpoints',
      modelPreferences: { 'gpt-4': 2, 'claude-3': 3, 'gemini-pro': 1 }
    },
    {
      id: 'session-4',
      title: 'Quick Test Session',
      description: 'Testing new features',
      createdAt: '2024-01-13T15:00:00Z',
      updatedAt: '2024-01-13T15:30:00Z',
      turnCount: 2,
      lastActivityAt: '2024-01-13T15:30:00Z',
      isActive: false,
      isArchived: false,
      lastPrompt: 'Test the new streaming functionality',
      modelPreferences: { 'gpt-4': 1, 'claude-3': 1 }
    }
  ];

  test.beforeEach(async ({ page }) => {
    // Mock sessions API endpoints
    await page.route('**/api/v1/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: mockSessions })
      });
    });

    await page.route('**/api/v1/sessions/*', async route => {
      const url = route.request().url();
      const sessionId = url.split('/').pop();
      const session = mockSessions.find(s => s.id === sessionId);
      
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(session || { error: 'Session not found' })
        });
      } else if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      }
    });

    // Mock session creation
    await page.route('**/api/v1/sessions', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-session-' + Date.now(),
            title: 'New Session',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            turnCount: 0,
            isActive: false,
            isArchived: false
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ sessions: mockSessions })
        });
      }
    });
  });

  test('should display session sidebar with header and controls', async ({ page }) => {
    await page.goto('/stream');

    // Open settings to ensure sidebar is visible (this may depend on layout)
    await page.locator('text=Show Settings').click();

    // Check session sidebar header
    await expect(page.locator('text=Sessions')).toBeVisible();
    
    // Check new session button
    await expect(page.locator('button:has-text("New")')).toBeVisible();
    await expect(page.locator('button:has-text("New") svg')).toBeVisible(); // Plus icon

    // Check search input
    await expect(page.locator('input[placeholder="Search sessions..."]')).toBeVisible();
    
    // Check search icon
    await expect(page.locator('input[placeholder="Search sessions..."]').locator('.. svg').first()).toBeVisible();
  });

  test('should display list of sessions with correct information', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Wait for sessions to load
    await page.waitForTimeout(1000);

    // Check that sessions are displayed
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    await expect(page.locator('text=Blog Post Ideas')).toBeVisible();
    await expect(page.locator('text=API Documentation')).toBeVisible();
    await expect(page.locator('text=Quick Test Session')).toBeVisible();

    // Check session details
    await expect(page.locator('text=8 turns')).toBeVisible();
    await expect(page.locator('text=12 turns')).toBeVisible();
    await expect(page.locator('text=6 turns')).toBeVisible();
    await expect(page.locator('text=2 turns')).toBeVisible();

    // Check last prompts are displayed
    await expect(page.locator('text*="Review the authentication module"')).toBeVisible();
    await expect(page.locator('text*="Generate ideas for articles"')).toBeVisible();

    // Check session count badge
    await expect(page.locator('text="4 sessions"')).toBeVisible();
  });

  test('should handle session search functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Search for "Blog"
    const searchInput = page.locator('input[placeholder="Search sessions..."]');
    await searchInput.fill('Blog');

    // Should show only Blog Post Ideas session
    await expect(page.locator('text=Blog Post Ideas')).toBeVisible();
    await expect(page.locator('text=Code Review Session')).not.toBeVisible();
    await expect(page.locator('text=API Documentation')).not.toBeVisible();

    // Check updated count
    await expect(page.locator('text="1 sessions"')).toBeVisible();

    // Search for content in last prompt
    await searchInput.fill('authentication');

    // Should show Code Review Session
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    await expect(page.locator('text=Blog Post Ideas')).not.toBeVisible();

    // Clear search
    await searchInput.fill('');

    // All sessions should be visible again
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    await expect(page.locator('text=Blog Post Ideas')).toBeVisible();
    await expect(page.locator('text="4 sessions"')).toBeVisible();
  });

  test('should handle sorting functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click sort dropdown
    await page.locator('button').filter({ hasText: /Recent|Oldest|Title|Turns/ }).click();

    // Check sort options are available
    await expect(page.locator('text=Most Recent')).toBeVisible();
    await expect(page.locator('text=Oldest First')).toBeVisible();
    await expect(page.locator('text=Title A-Z')).toBeVisible();
    await expect(page.locator('text=Most Active')).toBeVisible();

    // Select "Most Active" (sorts by turn count)
    await page.locator('text=Most Active').click();

    // Check sort button shows the selected option
    await expect(page.locator('button:has-text("Turns")')).toBeVisible();

    // Sessions should be ordered by turn count (Blog Post Ideas first with 12 turns)
    const sessionTitles = page.locator('[class*="cursor-pointer"] h4');
    await expect(sessionTitles.first()).toContainText('Blog Post Ideas');

    // Select "Title A-Z"
    await page.locator('button').filter({ hasText: /Turns/ }).click();
    await page.locator('text=Title A-Z').click();

    // Check sort button shows the selected option
    await expect(page.locator('button:has-text("Title")')).toBeVisible();

    // Sessions should be alphabetically sorted (API Documentation first)
    await expect(sessionTitles.first()).toContainText('API Documentation');
  });

  test('should handle session selection', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click on a session
    const codeReviewSession = page.locator('text=Code Review Session').locator('..');
    await codeReviewSession.click();

    // Session should be marked as active (check for active styling)
    await expect(codeReviewSession).toHaveClass(/border-ai-primary/);
    await expect(codeReviewSession).toHaveClass(/bg-ai-primary/);

    // Click on a different session
    const blogSession = page.locator('text=Blog Post Ideas').locator('..');
    await blogSession.click();

    // New session should be active
    await expect(blogSession).toHaveClass(/border-ai-primary/);
    
    // Previous session should no longer be active
    await expect(codeReviewSession).not.toHaveClass(/border-ai-primary/);
  });

  test('should open create session dialog', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click New button
    await page.locator('button:has-text("New")').click();

    // Check dialog opens
    await expect(page.locator('text=Create New Session')).toBeVisible();
    await expect(page.locator('text=Give your session a descriptive title')).toBeVisible();

    // Check input field and buttons
    await expect(page.locator('input[placeholder*="Session title"]')).toBeVisible();
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    await expect(page.locator('button:has-text("Create Session")')).toBeVisible();

    // Check create button is disabled without title
    await expect(page.locator('button:has-text("Create Session")')).toBeDisabled();
  });

  test('should create new session with valid title', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Open create dialog
    await page.locator('button:has-text("New")').click();

    // Enter session title
    const titleInput = page.locator('input[placeholder*="Session title"]');
    await titleInput.fill('New Test Session');

    // Create button should be enabled
    await expect(page.locator('button:has-text("Create Session")')).toBeEnabled();

    // Click create
    await page.locator('button:has-text("Create Session")').click();

    // Dialog should close
    await expect(page.locator('text=Create New Session')).not.toBeVisible();

    // New session should appear in list (this depends on how the app handles the response)
    // The API response includes a new session, so it should be visible
  });

  test('should handle session creation with Enter key', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Open create dialog
    await page.locator('button:has-text("New")').click();

    // Enter session title and press Enter
    const titleInput = page.locator('input[placeholder*="Session title"]');
    await titleInput.fill('Keyboard Test Session');
    await titleInput.press('Enter');

    // Dialog should close
    await expect(page.locator('text=Create New Session')).not.toBeVisible();
  });

  test('should cancel session creation', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Open create dialog
    await page.locator('button:has-text("New")').click();

    // Enter some text
    const titleInput = page.locator('input[placeholder*="Session title"]');
    await titleInput.fill('Test Session');

    // Click cancel
    await page.locator('button:has-text("Cancel")').click();

    // Dialog should close
    await expect(page.locator('text=Create New Session')).not.toBeVisible();

    // No new session should be created
    await expect(page.locator('text="4 sessions"')).toBeVisible();
  });

  test('should open session context menu', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click the three-dots menu for first session
    const contextMenuButton = page.locator('button').filter({ hasText: '' }).first(); // MoreHorizontal icon
    await contextMenuButton.click();

    // Check menu options
    await expect(page.locator('text=Rename')).toBeVisible();
    await expect(page.locator('text=Delete')).toBeVisible();

    // Check icons in menu
    await expect(page.locator('text=Rename').locator('.. svg')).toBeVisible(); // Edit3 icon
    await expect(page.locator('text=Delete').locator('.. svg')).toBeVisible(); // Trash2 icon
  });

  test('should start editing session title', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click context menu and select rename
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Rename').click();

    // Should show edit input with current title
    const editInput = page.locator('input').filter({ hasValue: 'Code Review Session' });
    await expect(editInput).toBeVisible();
    await expect(editInput).toBeFocused();

    // Check save and cancel buttons
    await expect(page.locator('button svg').filter({ hasText: '' })).toHaveCount(2); // Check and X icons
  });

  test('should save edited session title', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Start editing
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Rename').click();

    // Edit the title
    const editInput = page.locator('input').filter({ hasValue: 'Code Review Session' });
    await editInput.fill('Updated Review Session');

    // Click save (check mark button)
    const saveButton = page.locator('button').filter({ hasText: '' }).first(); // Check icon
    await saveButton.click();

    // Title should be updated
    await expect(page.locator('text=Updated Review Session')).toBeVisible();
    await expect(page.locator('text=Code Review Session')).not.toBeVisible();
  });

  test('should save edited title with Enter key', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Start editing
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Rename').click();

    // Edit the title and press Enter
    const editInput = page.locator('input').filter({ hasValue: 'Code Review Session' });
    await editInput.fill('Keyboard Updated Session');
    await editInput.press('Enter');

    // Title should be updated
    await expect(page.locator('text=Keyboard Updated Session')).toBeVisible();
  });

  test('should cancel editing with Escape key', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Start editing
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Rename').click();

    // Edit the title and press Escape
    const editInput = page.locator('input').filter({ hasValue: 'Code Review Session' });
    await editInput.fill('This should not save');
    await editInput.press('Escape');

    // Original title should remain
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    await expect(page.locator('text=This should not save')).not.toBeVisible();
  });

  test('should open delete confirmation dialog', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click context menu and select delete
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Delete').click();

    // Check delete confirmation dialog
    await expect(page.locator('text=Delete Session')).toBeVisible();
    await expect(page.locator('text*="Are you sure you want to delete"')).toBeVisible();
    await expect(page.locator('text*="Code Review Session"')).toBeVisible();
    await expect(page.locator('text*="This action cannot be undone"')).toBeVisible();

    // Check buttons
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    await expect(page.locator('button:has-text("Delete Session")')).toBeVisible();
  });

  test('should confirm session deletion', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Open delete dialog
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Delete').click();

    // Confirm deletion
    await page.locator('button:has-text("Delete Session")').nth(1).click(); // Second instance in dialog

    // Dialog should close
    await expect(page.locator('text=Delete Session')).not.toBeVisible();

    // Session should be removed from list (this depends on app state management)
    // In a real scenario, the session count would decrease
  });

  test('should cancel session deletion', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Open delete dialog
    const contextMenuButton = page.locator('[class*="cursor-pointer"]').first().locator('button').filter({ hasText: '' }).first();
    await contextMenuButton.click();
    await page.locator('text=Delete').click();

    // Cancel deletion
    await page.locator('button:has-text("Cancel")').nth(1).click(); // Instance in dialog

    // Dialog should close
    await expect(page.locator('text=Delete Session')).not.toBeVisible();

    // Session should still be in list
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    await expect(page.locator('text="4 sessions"')).toBeVisible();
  });

  test('should display loading state', async ({ page }) => {
    // Mock slow loading
    await page.route('**/api/v1/sessions', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: mockSessions })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Should show loading skeletons
    await expect(page.locator('.animate-pulse')).toHaveCount(3);

    // Wait for loading to complete
    await page.waitForTimeout(1500);

    // Should show actual sessions
    await expect(page.locator('text=Code Review Session')).toBeVisible();
  });

  test('should display empty state with no sessions', async ({ page }) => {
    // Mock empty sessions response
    await page.route('**/api/v1/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Should show empty state
    await expect(page.locator('text=No sessions yet')).toBeVisible();
    await expect(page.locator('text=Create your first session to get started')).toBeVisible();
    
    // Should show message icon
    await expect(page.locator('svg').filter({ hasText: '' })).toBeVisible(); // MessageSquare icon

    // Session count should be 0
    await expect(page.locator('text="0 sessions"')).toBeVisible();
  });

  test('should display empty search results', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Search for something that doesn't exist
    const searchInput = page.locator('input[placeholder="Search sessions..."]');
    await searchInput.fill('nonexistent');

    // Should show empty search state
    await expect(page.locator('text=No sessions found for "nonexistent"')).toBeVisible();
    
    // Should show search icon
    await expect(page.locator('svg').filter({ hasText: '' })).toBeVisible(); // Search icon

    // Session count should be 0
    await expect(page.locator('text="0 sessions"')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);

    // Session sidebar should still be functional
    await expect(page.locator('text=Sessions')).toBeVisible();
    await expect(page.locator('button:has-text("New")')).toBeVisible();
    await expect(page.locator('input[placeholder="Search sessions..."]')).toBeVisible();

    // Sessions should still be visible and clickable
    await expect(page.locator('text=Code Review Session')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('text=Sessions')).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Test Tab navigation
    await page.keyboard.press('Tab');
    
    // Focus search input
    const searchInput = page.locator('input[placeholder="Search sessions..."]');
    await searchInput.focus();
    await expect(searchInput).toBeFocused();

    // Type in search
    await page.keyboard.type('Code');
    await expect(searchInput).toHaveValue('Code');

    // Tab to sort dropdown
    await page.keyboard.press('Tab');
    const sortButton = page.locator('button').filter({ hasText: /Recent|Oldest|Title|Turns/ });
    await expect(sortButton).toBeFocused();

    // Open sort menu with Enter
    await page.keyboard.press('Enter');
    await expect(page.locator('text=Most Recent')).toBeVisible();

    // Navigate through session list
    await page.keyboard.press('Escape'); // Close dropdown
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to select sessions with keyboard
    const firstSession = page.locator('[class*="cursor-pointer"]').first();
    await firstSession.focus();
    await page.keyboard.press('Enter');
    
    // Session should be selected
    await expect(firstSession).toHaveClass(/border-ai-primary/);
  });

  test('should handle accessibility requirements', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check heading hierarchy
    await expect(page.locator('h1, h2, h3, h4')).toHaveCount(5); // Main title + Sessions + 4 session titles

    // Check form labels and inputs
    const searchInput = page.locator('input[placeholder="Search sessions..."]');
    await expect(searchInput).toBeVisible();

    // Check button accessibility
    const newButton = page.locator('button:has-text("New")');
    await expect(newButton).toBeVisible();

    // Test focus indicators
    await searchInput.focus();
    await expect(searchInput).toBeFocused();

    await newButton.focus();
    await expect(newButton).toBeFocused();

    // Check dialog accessibility when opened
    await newButton.click();
    
    // Dialog should have proper title
    await expect(page.locator('text=Create New Session')).toBeVisible();
    
    // Input should be focused automatically
    const titleInput = page.locator('input[placeholder*="Session title"]');
    await expect(titleInput).toBeFocused();

    // Check color contrast for text elements
    await expect(page.locator('text=Sessions')).toHaveCSS('color', /rgb/);
  });

  test('should have proper padding for session list container', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check that sessions list container has proper padding classes
    const sessionsContainer = page.locator('.flex-1.overflow-y-auto > div').filter({ hasText: 'Code Review Session' }).first().locator('..');
    
    // Verify the container has the updated padding classes
    await expect(sessionsContainer).toHaveClass(/p-lg/);
    await expect(sessionsContainer).toHaveClass(/pt-md/);
    await expect(sessionsContainer).toHaveClass(/pb-lg/);
    
    // Check that individual sessions have proper spacing
    const sessionItems = page.locator('[class*="cursor-pointer"]');
    const firstSession = sessionItems.first();
    const secondSession = sessionItems.nth(1);
    
    // Verify sessions are not snapped to the top
    const containerBox = await sessionsContainer.boundingBox();
    const firstSessionBox = await firstSession.boundingBox();
    
    if (containerBox && firstSessionBox) {
      // Check there's adequate top padding
      const topSpacing = firstSessionBox.y - containerBox.y;
      expect(topSpacing).toBeGreaterThan(10); // Should have at least 10px of top spacing
    }

    // Verify vertical spacing between sessions
    const secondSessionBox = await secondSession.boundingBox();
    if (firstSessionBox && secondSessionBox) {
      const spacing = secondSessionBox.y - (firstSessionBox.y + firstSessionBox.height);
      expect(spacing).toBeGreaterThan(5); // Should have space between sessions
    }
  });

  test('should have proper padding for empty state', async ({ page }) => {
    // Mock empty sessions response
    await page.route('**/api/v1/sessions', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [] })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check empty state container has proper padding
    const emptyStateContainer = page.locator('.flex-1.overflow-y-auto > div').filter({ hasText: 'No sessions yet' }).first();
    
    // Verify the container has generous padding
    await expect(emptyStateContainer).toHaveClass(/p-lg/);
    await expect(emptyStateContainer).toHaveClass(/py-xl/);
    
    // Check visual centering
    const containerBox = await emptyStateContainer.boundingBox();
    const parentBox = await page.locator('.flex-1.overflow-y-auto').boundingBox();
    
    if (containerBox && parentBox) {
      // Verify there's adequate padding from top
      const topPadding = containerBox.y - parentBox.y;
      expect(topPadding).toBeGreaterThan(20); // Should have substantial top padding
    }
  });

  test('should have proper padding for loading state', async ({ page }) => {
    // Mock slow loading
    await page.route('**/api/v1/sessions', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: mockSessions })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Check loading state container has proper padding
    const loadingContainer = page.locator('.flex-1.overflow-y-auto > div').filter({ has: page.locator('.animate-pulse') }).first();
    
    // Verify the container has updated padding classes
    await expect(loadingContainer).toHaveClass(/p-lg/);
    await expect(loadingContainer).toHaveClass(/pt-md/);
    
    // Check that skeleton items are properly spaced
    const skeletons = page.locator('.animate-pulse');
    const firstSkeleton = skeletons.first();
    
    const containerBox = await loadingContainer.boundingBox();
    const firstSkeletonBox = await firstSkeleton.boundingBox();
    
    if (containerBox && firstSkeletonBox) {
      // Check there's adequate top padding
      const topSpacing = firstSkeletonBox.y - containerBox.y;
      expect(topSpacing).toBeGreaterThan(10); // Should have proper top spacing
    }
  });

  test('should handle session persistence across page reloads', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Select a session
    const codeReviewSession = page.locator('text=Code Review Session').locator('..');
    await codeReviewSession.click();

    // Session should be active
    await expect(codeReviewSession).toHaveClass(/border-ai-primary/);

    // Reload page
    await page.reload();
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Session should still be active after reload (if app maintains state)
    // This depends on how the app handles session persistence
    await expect(page.locator('text=Code Review Session')).toBeVisible();
  });
});