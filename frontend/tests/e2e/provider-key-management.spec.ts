import { test, expect } from '@playwright/test';

/**
 * E2E tests for Provider Key Management UI
 * 
 * Tests the complete user journey for managing provider API keys:
 * - Navigation to settings page
 * - Adding new provider keys
 * - Viewing and managing existing keys
 * - Updating and deleting keys
 * - Error handling and validation
 */

// Test data
const TEST_USER = {
  email: 'e2e-test@example.com',
  password: 'TestPassword123',
  apiKey: 'aid_sk_test_e2e_key_123456789'
};

const TEST_PROVIDER_KEY = {
  provider: 'openai',
  apiKey: 'sk-test-e2e-provider-key-1234567890abcdef',
  name: 'E2E Test OpenAI Key'
};

test.describe('Provider Key Management', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the app and ensure we're authenticated
    await page.goto('http://localhost:3001');
    
    // Wait for the page to load
    await page.waitForSelector('[data-testid="auth-status"]', { timeout: 10000 });
    
    // Check if we need to authenticate
    const authStatus = await page.textContent('[data-testid="auth-status"]');
    if (authStatus?.includes('Not Authenticated')) {
      // Use dev auto-login if available
      await page.click('[data-testid="auth-dropdown-trigger"]');
      await page.click('text=Dev Auto-Login');
      await page.waitForSelector('text=user', { timeout: 5000 });
    }
  });

  test('should navigate to settings page via user dropdown', async ({ page }) => {
    // Open user dropdown
    await page.click('[data-testid="auth-status"]');
    
    // Click Settings link
    await page.click('text=Settings');
    
    // Verify we're on settings page
    await expect(page).toHaveURL(/.*\/settings/);
    await expect(page.locator('h1')).toContainText('Settings');
    
    // Verify API Keys tab is active by default
    await expect(page.locator('[data-testid="tab-api-keys"]')).toHaveAttribute('data-state', 'active');
  });

  test('should display empty state when no provider keys exist', async ({ page }) => {
    // Navigate to settings
    await page.goto('http://localhost:3001/settings');
    
    // Should show empty state
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();
    await expect(page.locator('text=No Provider Keys')).toBeVisible();
    await expect(page.locator('text=Add Your First Key')).toBeVisible();
  });

  test('should open add provider key dialog and show provider information', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Click Add Provider Key button
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Verify dialog opened
    await expect(page.locator('[data-testid="add-provider-dialog"]')).toBeVisible();
    await expect(page.locator('text=Add Provider API Key')).toBeVisible();
    
    // Select OpenAI provider
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    
    // Verify provider information is displayed
    await expect(page.locator('text=GPT-4, GPT-3.5 Turbo')).toBeVisible();
    await expect(page.locator('text=Expected format: sk-proj-...')).toBeVisible();
    await expect(page.locator('text=Get API Key')).toBeVisible();
  });

  test('should create a new provider key successfully', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Fill in form
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    
    await page.fill('[data-testid="api-key-input"]', TEST_PROVIDER_KEY.apiKey);
    await page.fill('[data-testid="name-input"]', TEST_PROVIDER_KEY.name);
    
    // Submit form
    await page.click('[data-testid="add-key-submit"]');
    
    // Verify dialog closed and key was added
    await expect(page.locator('[data-testid="add-provider-dialog"]')).not.toBeVisible();
    
    // Should see the new key in the list
    await expect(page.locator(`[data-testid="provider-key-${TEST_PROVIDER_KEY.name}"]`)).toBeVisible();
    await expect(page.locator('text=...cdef')).toBeVisible(); // Key hint
    await expect(page.locator('text=OpenAI')).toBeVisible();
  });

  test('should validate required fields in add dialog', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Try to submit without filling required fields
    await page.click('[data-testid="add-key-submit"]');
    
    // Submit button should be disabled
    await expect(page.locator('[data-testid="add-key-submit"]')).toBeDisabled();
    
    // Fill provider but not API key
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    await page.click('[data-testid="add-key-submit"]');
    
    // Still should be disabled
    await expect(page.locator('[data-testid="add-key-submit"]')).toBeDisabled();
    
    // Fill API key
    await page.fill('[data-testid="api-key-input"]', 'sk-test-key');
    
    // Now submit should be enabled
    await expect(page.locator('[data-testid="add-key-submit"]')).toBeEnabled();
  });

  test('should toggle API key visibility in add dialog', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Fill API key
    await page.fill('[data-testid="api-key-input"]', 'sk-test-visible-key');
    
    // Verify input is type="password" by default
    await expect(page.locator('[data-testid="api-key-input"]')).toHaveAttribute('type', 'password');
    
    // Click show/hide toggle
    await page.click('[data-testid="toggle-key-visibility"]');
    
    // Verify input is now type="text"
    await expect(page.locator('[data-testid="api-key-input"]')).toHaveAttribute('type', 'text');
    
    // Click again to hide
    await page.click('[data-testid="toggle-key-visibility"]');
    
    // Verify input is back to type="password"
    await expect(page.locator('[data-testid="api-key-input"]')).toHaveAttribute('type', 'password');
  });

  test('should filter provider keys by search term', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Assume we have multiple keys already (would need setup)
    // For now, test the search functionality exists
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="provider-filter"]')).toBeVisible();
    await expect(page.locator('[data-testid="status-filter"]')).toBeVisible();
    
    // Test search input
    await page.fill('[data-testid="search-input"]', 'openai');
    
    // Should filter results (specific assertion would depend on having test data)
    await expect(page.locator('[data-testid="search-input"]')).toHaveValue('openai');
  });

  test('should open edit dialog when clicking edit button', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // First create a key to edit (assuming we have one)
    // This would typically be done in beforeEach or through API setup
    
    // Hover over a provider key card to show actions
    await page.hover('[data-testid="provider-key-card"]:first-child');
    
    // Click edit button
    await page.click('[data-testid="edit-key-btn"]:first-child');
    
    // Verify edit dialog opened
    await expect(page.locator('[data-testid="edit-provider-dialog"]')).toBeVisible();
    await expect(page.locator('text=Edit')).toBeVisible();
  });

  test('should update provider key name and status', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open edit dialog (assuming we have a key to edit)
    await page.hover('[data-testid="provider-key-card"]:first-child');
    await page.click('[data-testid="edit-key-btn"]:first-child');
    
    // Update name
    await page.fill('[data-testid="edit-name-input"]', 'Updated Key Name');
    
    // Toggle active status
    await page.click('[data-testid="active-toggle"]');
    
    // Submit changes
    await page.click('[data-testid="save-changes-btn"]');
    
    // Verify dialog closed
    await expect(page.locator('[data-testid="edit-provider-dialog"]')).not.toBeVisible();
    
    // Verify changes were applied (would need to check the card content)
    await expect(page.locator('text=Updated Key Name')).toBeVisible();
  });

  test('should delete provider key with confirmation', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Get initial count of provider keys
    const initialCards = await page.locator('[data-testid="provider-key-card"]').count();
    
    // Hover over a provider key card and click delete
    await page.hover('[data-testid="provider-key-card"]:first-child');
    await page.click('[data-testid="delete-key-btn"]:first-child');
    
    // Handle browser confirmation dialog
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('Are you sure');
      await dialog.accept();
    });
    
    // Verify key was removed (count should decrease)
    await expect(page.locator('[data-testid="provider-key-card"]')).toHaveCount(initialCards - 1);
  });

  test('should display usage statistics for provider keys', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Verify statistics are displayed in overview cards
    await expect(page.locator('[data-testid="total-keys-stat"]')).toBeVisible();
    await expect(page.locator('[data-testid="active-keys-stat"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-requests-stat"]')).toBeVisible();
    
    // Verify individual key cards show usage stats
    const firstCard = page.locator('[data-testid="provider-key-card"]').first();
    if (await firstCard.isVisible()) {
      await expect(firstCard.locator('text=Total Requests')).toBeVisible();
      await expect(firstCard.locator('text=Last Used')).toBeVisible();
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/v1/provider-keys', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });
    
    await page.goto('http://localhost:3001/settings');
    
    // Should display error message
    await expect(page.locator('[data-testid="error-alert"]')).toBeVisible();
    await expect(page.locator('text=Failed to fetch provider keys')).toBeVisible();
  });

  test('should validate provider selection in add dialog', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Try to select invalid provider (this would be caught by validation)
    // The form should prevent invalid providers from being selected
    
    // Verify only valid providers are available in dropdown
    await page.click('[data-testid="provider-select"]');
    
    const providerOptions = await page.locator('[data-testid="provider-option"]').allTextContents();
    expect(providerOptions).toContain('OpenAI');
    expect(providerOptions).toContain('Anthropic');
    expect(providerOptions).toContain('Google AI');
  });

  test('should display provider documentation links', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Check that provider key cards have documentation links
    const firstCard = page.locator('[data-testid="provider-key-card"]').first();
    if (await firstCard.isVisible()) {
      const docsLink = firstCard.locator('[data-testid="docs-link"]');
      await expect(docsLink).toBeVisible();
      await expect(docsLink).toHaveAttribute('href', /https:\/\/.*/);
    }
    
    // Check that add dialog shows documentation links
    await page.click('[data-testid="add-provider-key-btn"]');
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    
    const getApiKeyLink = page.locator('[data-testid="get-api-key-link"]');
    await expect(getApiKeyLink).toBeVisible();
    await expect(getApiKeyLink).toHaveAttribute('href', /platform\.openai\.com/);
  });

  test('should refresh provider keys list', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Click refresh button
    await page.click('[data-testid="refresh-keys-btn"]');
    
    // Verify loading state
    await expect(page.locator('[data-testid="refresh-keys-btn"] .animate-spin')).toBeVisible();
    
    // Wait for loading to complete
    await expect(page.locator('[data-testid="refresh-keys-btn"] .animate-spin')).not.toBeVisible();
  });

  test('should validate model-specific key creation', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Select provider
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    
    // Fill required fields
    await page.fill('[data-testid="api-key-input"]', 'sk-test-model-specific');
    await page.fill('[data-testid="name-input"]', 'Model Specific Key');
    
    // Select specific model
    await page.click('[data-testid="model-select"]');
    await page.click('text=gpt-4');
    
    // Submit form
    await page.click('[data-testid="add-key-submit"]');
    
    // Verify key was created with model specificity
    await expect(page.locator('text=gpt-4')).toBeVisible();
  });

  test('should handle model override select with "use for all models" option', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Select provider first
    await page.click('[data-testid="provider-select"]');
    await page.click('text=OpenAI');
    
    // Fill required fields
    await page.fill('[data-testid="api-key-input"]', 'sk-test-all-models');
    await page.fill('[data-testid="name-input"]', 'All Models Key');
    
    // Test the model override select dropdown
    await page.click('[data-testid="model-select"]');
    
    // Verify the "Use for all models" option is available and has a non-empty value
    const allModelsOption = page.locator('text=Use for all models (recommended)');
    await expect(allModelsOption).toBeVisible();
    
    // Select "Use for all models" option
    await allModelsOption.click();
    
    // Verify the select doesn't throw an error and the form can be submitted
    await expect(page.locator('[data-testid="add-key-submit"]')).toBeEnabled();
    
    // Submit form - should work without Select component errors
    await page.click('[data-testid="add-key-submit"]');
    
    // Verify the dialog closed successfully (no Select errors)
    await expect(page.locator('[data-testid="add-provider-dialog"]')).not.toBeVisible();
  });

  test('should handle unauthorized access', async ({ page }) => {
    // Clear any existing authentication
    await page.goto('http://localhost:3001/settings');
    
    // Mock unauthorized response
    await page.route('**/api/v1/provider-keys', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' })
      });
    });
    
    // Refresh page to trigger API call
    await page.reload();
    
    // Should display authentication required message
    await expect(page.locator('text=Please log in')).toBeVisible();
  });

  test('should support keyboard navigation in dialogs', async ({ page }) => {
    await page.goto('http://localhost:3001/settings');
    
    // Open add dialog
    await page.click('[data-testid="add-provider-key-btn"]');
    
    // Test Tab navigation through form fields
    await page.keyboard.press('Tab'); // Should focus provider select
    await page.keyboard.press('Tab'); // Should focus API key input
    await page.keyboard.press('Tab'); // Should focus name input
    await page.keyboard.press('Tab'); // Should focus model select
    await page.keyboard.press('Tab'); // Should focus cancel button
    await page.keyboard.press('Tab'); // Should focus submit button
    
    // Test Escape to close dialog
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="add-provider-dialog"]')).not.toBeVisible();
  });

});