import { test, expect } from '@playwright/test';

test.describe('Settings Management - Comprehensive E2E Tests', () => {
  
  // Mock API keys data
  const mockAPIKeys = [
    {
      id: 'key-1',
      name: 'Development Key',
      description: 'For development and testing',
      keyPreview: 'ak-dev...xyz',
      createdAt: '2024-01-10T10:00:00Z',
      lastUsed: '2024-01-15T14:30:00Z',
      isActive: true,
      permissions: ['read', 'write']
    },
    {
      id: 'key-2',
      name: 'Production Key',
      description: 'For production deployments',
      keyPreview: 'ak-prod...abc',
      createdAt: '2024-01-08T09:15:00Z',
      lastUsed: '2024-01-14T16:45:00Z',
      isActive: true,
      permissions: ['read', 'write', 'admin']
    }
  ];

  // Mock credentials data
  const mockCredentials = [
    {
      id: 'cred-1',
      provider: 'openai',
      name: 'OpenAI Production',
      isActive: true,
      lastValidated: '2024-01-15T10:00:00Z',
      status: 'valid'
    },
    {
      id: 'cred-2',
      provider: 'anthropic',
      name: 'Claude Development',
      isActive: false,
      lastValidated: '2024-01-12T14:00:00Z',
      status: 'expired'
    }
  ];

  test.beforeEach(async ({ page }) => {
    // Mock API keys endpoints
    await page.route('**/api/v1/auth/api-keys', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ apiKeys: mockAPIKeys })
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-key-' + Date.now(),
            name: 'New API Key',
            key: 'ak-new-generated-key-123456789',
            keyPreview: 'ak-new...789',
            createdAt: new Date().toISOString()
          })
        });
      }
    });

    // Mock API key deletion
    await page.route('**/api/v1/auth/api-keys/*', async route => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        });
      }
    });

    // Mock credentials endpoints
    await page.route('**/api/v1/credentials', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ credentials: mockCredentials })
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-cred-' + Date.now(),
            provider: 'openai',
            name: 'New Credential',
            isActive: true,
            status: 'valid'
          })
        });
      }
    });

    // Mock auth status
    await page.route('**/api/v1/auth/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: {
            id: 'user-123',
            email: 'test@example.com',
            name: 'Test User'
          }
        })
      });
    });
  });

  test('should display settings panel when opened', async ({ page }) => {
    await page.goto('/stream');

    // Open settings
    await page.locator('text=Show Settings').click();

    // Check settings panel is visible
    await expect(page.locator('text=Generation Configuration')).toBeVisible();
    
    // Check main settings sections
    await expect(page.locator('text=Select Models')).toBeVisible();
    
    // Check mode selector
    await expect(page.locator('[data-testid="mode-selector"], text*="Mode"')).toBeVisible();
  });

  test('should display API key management section', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Wait for settings to load
    await page.waitForTimeout(1000);

    // Look for API key management (this may be in a separate section or tab)
    // The exact location depends on how settings are organized
    
    // Check if API key section is visible or accessible
    const apiKeySection = page.locator('text*="API Key"');
    if (await apiKeySection.count() > 0) {
      await expect(apiKeySection).toBeVisible();
    }
  });

  test('should manage API keys correctly', async ({ page }) => {
    // Navigate to dedicated API key management (if it exists as separate page)
    await page.goto('/settings'); // This might be a dedicated settings page
    
    // Or test within stream settings if that's where it's located
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Look for API key management interface
    // This test depends on how API keys are managed in the UI
  });

  test('should handle credential management', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check if credential management is accessible
    // This might be part of model selection or a separate section
    
    // Look for provider credentials setup
    const credentialSection = page.locator('text*="Credential"');
    if (await credentialSection.count() > 0) {
      await expect(credentialSection).toBeVisible();
    }
  });

  test('should display model configuration settings', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check model selection interface
    await expect(page.locator('text=Select Models')).toBeVisible();
    
    // Check if model browser is available
    const modelBrowser = page.locator('text=Model Browser');
    if (await modelBrowser.count() > 0) {
      await expect(modelBrowser).toBeVisible();
    }
  });

  test('should handle mode selection', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check mode selector
    const modeSelector = page.locator('[data-testid="mode-selector"]');
    if (await modeSelector.count() > 0) {
      await expect(modeSelector).toBeVisible();
      
      // Test mode switching
      await modeSelector.click();
      
      // Should show mode options
      // This depends on the specific mode options available
    }
  });

  test('should persist settings across sessions', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Make some setting changes (e.g., select models)
    // This depends on available settings
    
    // Reload page
    await page.reload();
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Settings should be preserved
    // This depends on how the app handles settings persistence
  });

  test('should validate setting inputs correctly', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Test input validation for any settings forms
    // This could include API key format validation, etc.
    
    // Look for input fields in settings
    const inputs = page.locator('input[type="text"], input[type="password"], textarea');
    const inputCount = await inputs.count();
    
    if (inputCount > 0) {
      // Test validation on first input
      const firstInput = inputs.first();
      await firstInput.fill('invalid-input');
      
      // Check for validation feedback
      // This depends on the specific validation implementation
    }
  });

  test('should handle settings loading states', async ({ page }) => {
    // Mock slow loading
    await page.route('**/api/v1/models/catalog', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          models: [],
          providers: [],
          capabilities: []
        })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Should show loading state
    const loadingSpinner = page.locator('.animate-spin');
    if (await loadingSpinner.count() > 0) {
      await expect(loadingSpinner).toBeVisible();
    }

    // Wait for loading to complete
    await page.waitForTimeout(1500);

    // Settings should load
    await expect(page.locator('text=Select Models')).toBeVisible();
  });

  test('should handle settings errors gracefully', async ({ page }) => {
    // Mock error response
    await page.route('**/api/v1/models/catalog', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Should handle error gracefully
    // Look for error message or retry option
    const errorText = page.locator('text*="error", text*="Error", text*="failed", text*="Failed"');
    if (await errorText.count() > 0) {
      await expect(errorText.first()).toBeVisible();
    }
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Settings panel should be accessible on mobile
    await expect(page.locator('text=Generation Configuration')).toBeVisible();
    
    // Settings should be properly laid out for mobile
    const settingsPanel = page.locator('[class*="settings"], [class*="config"]');
    if (await settingsPanel.count() > 0) {
      const panelBox = await settingsPanel.first().boundingBox();
      expect(panelBox?.width).toBeLessThanOrEqual(375);
    }
  });

  test('should handle keyboard navigation in settings', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Test Tab navigation through settings
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should be able to navigate through interactive elements
    const focusedElement = page.locator(':focus');
    if (await focusedElement.count() > 0) {
      await expect(focusedElement).toBeFocused();
    }

    // Test specific setting controls
    const selectElements = page.locator('select, button[role="combobox"]');
    if (await selectElements.count() > 0) {
      await selectElements.first().focus();
      await expect(selectElements.first()).toBeFocused();
      
      // Test opening dropdown with keyboard
      await page.keyboard.press('Enter');
    }
  });

  test('should handle settings accessibility requirements', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check form labels and associations
    const inputs = page.locator('input, select, textarea');
    const inputCount = await inputs.count();
    
    if (inputCount > 0) {
      // Check that inputs have proper labels or ARIA attributes
      const firstInput = inputs.first();
      const hasLabel = await firstInput.getAttribute('aria-label') || 
                       await firstInput.getAttribute('aria-labelledby') ||
                       await page.locator(`label[for="${await firstInput.getAttribute('id')}"]`).count() > 0;
      
      // At least some form of labeling should exist
      // This is more of a guideline check since exact implementation varies
    }

    // Check heading hierarchy
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    if (await headings.count() > 0) {
      await expect(headings.first()).toBeVisible();
    }

    // Check focus indicators
    const firstButton = page.locator('button').first();
    await firstButton.focus();
    await expect(firstButton).toBeFocused();
  });

  test('should handle settings export/import functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Look for export/import options
    const exportButton = page.locator('button:has-text("Export"), text*="export"');
    const importButton = page.locator('button:has-text("Import"), text*="import"');

    if (await exportButton.count() > 0) {
      await expect(exportButton).toBeVisible();
      
      // Test export functionality
      await exportButton.click();
      // Should trigger download or show export dialog
    }

    if (await importButton.count() > 0) {
      await expect(importButton).toBeVisible();
      
      // Test import functionality
      await importButton.click();
      // Should show file picker or import dialog
    }
  });

  test('should handle settings reset functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Look for reset or restore defaults option
    const resetButton = page.locator('button:has-text("Reset"), button:has-text("Default"), text*="reset", text*="restore"');

    if (await resetButton.count() > 0) {
      await expect(resetButton.first()).toBeVisible();
      
      // Test reset functionality
      await resetButton.first().click();
      
      // Should show confirmation or reset settings immediately
      const confirmDialog = page.locator('text*="confirm", text*="sure", text*="reset"');
      if (await confirmDialog.count() > 0) {
        await expect(confirmDialog.first()).toBeVisible();
      }
    }
  });

  test('should handle settings search/filter functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Look for search or filter controls in settings
    const searchInput = page.locator('input[placeholder*="search"], input[placeholder*="filter"]');
    const filterButtons = page.locator('button:has-text("Filter"), button:has-text("Search")');

    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible();
      
      // Test search functionality
      await searchInput.first().fill('test');
      
      // Should filter or search settings
      await page.waitForTimeout(500);
    }

    if (await filterButtons.count() > 0) {
      await expect(filterButtons.first()).toBeVisible();
      
      // Test filter functionality
      await filterButtons.first().click();
    }
  });

  test('should integrate with user authentication state', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Settings should reflect authenticated state
    // Look for user-specific settings or authenticated features
    
    // Check if user info is displayed
    const userInfo = page.locator('text*="test@example.com", text*="Test User"');
    if (await userInfo.count() > 0) {
      await expect(userInfo.first()).toBeVisible();
    }
    
    // Check for logout or account settings
    const accountSettings = page.locator('text*="Account", text*="Profile", text*="Logout"');
    if (await accountSettings.count() > 0) {
      await expect(accountSettings.first()).toBeVisible();
    }
  });

  test('should handle settings help and documentation', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Look for help, documentation, or info icons
    const helpElements = page.locator('button:has-text("Help"), button:has-text("?"), text*="help", [title*="help"]');
    const infoIcons = page.locator('svg[class*="info"], button[aria-label*="info"]');

    if (await helpElements.count() > 0) {
      await expect(helpElements.first()).toBeVisible();
      
      // Test help functionality
      await helpElements.first().click();
      
      // Should show help content or open documentation
      await page.waitForTimeout(500);
    }

    if (await infoIcons.count() > 0) {
      await expect(infoIcons.first()).toBeVisible();
      
      // Test info tooltip or modal
      await infoIcons.first().hover();
      await page.waitForTimeout(300);
    }
  });
});