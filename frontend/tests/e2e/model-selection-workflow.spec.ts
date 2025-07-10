import { test, expect } from '@playwright/test';

test.describe('Model Selection Workflow - Comprehensive E2E Tests', () => {
  
  // Mock model catalog data
  const mockModelCatalog = {
    models: [
      {
        id: 'gpt-4-model-1',
        provider: 'openai',
        model_name: 'gpt-4',
        litellm_model_name: 'openai/gpt-4',
        display_name: 'GPT-4',
        description: 'Advanced reasoning, complex problem solving',
        context_window: 128000,
        max_output_tokens: 4096,
        input_price_per_1m_tokens: 30.0,
        output_price_per_1m_tokens: 60.0,
        capabilities: ['text_completion', 'chat_completion', 'function_calling', 'streaming'],
        requires_api_key: true,
        requires_region: false,
        requires_project_id: false,
        is_active: true
      },
      {
        id: 'claude-3-model-1',
        provider: 'anthropic',
        model_name: 'claude-3-opus',
        litellm_model_name: 'anthropic/claude-3-opus-20240229',
        display_name: 'Claude 3 Opus',
        description: 'Most powerful Claude model for complex tasks',
        context_window: 200000,
        max_output_tokens: 4096,
        input_price_per_1m_tokens: 15.0,
        output_price_per_1m_tokens: 75.0,
        capabilities: ['text_completion', 'chat_completion', 'vision', 'streaming'],
        requires_api_key: true,
        requires_region: false,
        requires_project_id: false,
        is_active: true
      },
      {
        id: 'gemini-pro-model-1',
        provider: 'gemini',
        model_name: 'gemini-pro',
        litellm_model_name: 'gemini/gemini-pro',
        display_name: 'Gemini Pro',
        description: 'Google\'s most capable AI model',
        context_window: 32000,
        max_output_tokens: 8192,
        input_price_per_1m_tokens: 0.5,
        output_price_per_1m_tokens: 1.5,
        capabilities: ['text_completion', 'chat_completion', 'vision', 'function_calling'],
        requires_api_key: true,
        requires_region: false,
        requires_project_id: true,
        is_active: true
      },
      {
        id: 'llama-2-model-1',
        provider: 'ollama',
        model_name: 'llama2',
        litellm_model_name: 'ollama/llama2',
        display_name: 'Llama 2 7B',
        description: 'Open source foundation model',
        context_window: 4096,
        max_output_tokens: 2048,
        input_price_per_1m_tokens: 0,
        output_price_per_1m_tokens: 0,
        capabilities: ['text_completion', 'chat_completion'],
        requires_api_key: false,
        requires_region: false,
        requires_project_id: false,
        is_active: true
      }
    ],
    providers: [
      {
        provider: 'openai',
        display_name: 'OpenAI',
        description: 'GPT-4, GPT-3.5 and other OpenAI models',
        requires_api_key: true,
        model_count: 8,
        user_has_credentials: true
      },
      {
        provider: 'anthropic',
        display_name: 'Anthropic',
        description: 'Claude family of models',
        requires_api_key: true,
        model_count: 4,
        user_has_credentials: false
      },
      {
        provider: 'gemini',
        display_name: 'Google Gemini',
        description: 'Google\'s Gemini AI models',
        requires_api_key: true,
        model_count: 3,
        user_has_credentials: true
      },
      {
        provider: 'ollama',
        display_name: 'Ollama',
        description: 'Local open source models',
        requires_api_key: false,
        model_count: 12,
        user_has_credentials: false
      }
    ],
    capabilities: [
      'text_completion',
      'chat_completion',
      'vision',
      'function_calling',
      'streaming',
      'embedding',
      'image_generation'
    ]
  };

  test.beforeEach(async ({ page }) => {
    // Mock model catalog API
    await page.route('**/api/v1/models/catalog', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockModelCatalog)
      });
    });
  });

  test('should load model selector with catalog data', async ({ page }) => {
    await page.goto('/stream');
    
    // Open settings to access model selector
    await page.locator('text=Show Settings').click();

    // Wait for model catalog to load
    await page.waitForTimeout(1000);

    // Check model browser is visible
    await expect(page.locator('text=Model Browser')).toBeVisible();

    // Check search functionality
    await expect(page.locator('input[placeholder="Search models..."]')).toBeVisible();

    // Check filter dropdowns
    await expect(page.locator('text=All Providers')).toBeVisible();
    await expect(page.locator('text=All Capabilities')).toBeVisible();

    // Check view tabs
    await expect(page.locator('button[role="tab"]:has-text("By Provider")')).toBeVisible();
    await expect(page.locator('button[role="tab"]:has-text("All Models")')).toBeVisible();
  });

  test('should display models grouped by provider', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Should default to "By Provider" view
    await expect(page.locator('button[role="tab"]:has-text("By Provider")[aria-selected="true"]')).toBeVisible();

    // Check provider sections
    await expect(page.locator('text=OpenAI')).toBeVisible();
    await expect(page.locator('text=Anthropic')).toBeVisible();
    await expect(page.locator('text=Google Gemini')).toBeVisible();
    await expect(page.locator('text=Ollama')).toBeVisible();

    // Check provider status badges
    await expect(page.locator('text=Connected')).toBeVisible(); // OpenAI and Gemini
    await expect(page.locator('text=Setup Required')).toBeVisible(); // Anthropic

    // Check model count display
    await expect(page.locator('text*="models"')).toHaveCount(4); // One for each provider
  });

  test('should display individual model cards correctly', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check GPT-4 model card
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Advanced reasoning, complex problem solving')).toBeVisible();
    await expect(page.locator('text=$30/1M tokens')).toBeVisible();
    await expect(page.locator('text=128,000 context')).toBeVisible();

    // Check Claude model card
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
    await expect(page.locator('text=Most powerful Claude model for complex tasks')).toBeVisible();

    // Check Llama model card (free model)
    await expect(page.locator('text=Llama 2 7B')).toBeVisible();
    await expect(page.locator('text=Free')).toBeVisible();

    // Check capabilities icons are present
    const modelCards = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await expect(modelCards.locator('svg').first()).toBeVisible();
  });

  test('should handle model selection and variant creation', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Select GPT-4 model
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    // Check selected variants section appears
    await expect(page.locator('text=Selected Model Variants (1/5)')).toBeVisible();

    // Check variant card appears
    await expect(page.locator('text=GPT-4').nth(1)).toBeVisible(); // Second instance in selected variants
    await expect(page.locator('text=OpenAI').nth(1)).toBeVisible(); // Provider in variant card

    // Check default parameters are shown
    await expect(page.locator('text*="T: 0.7"')).toBeVisible(); // Temperature
    await expect(page.locator('text*="Max: 1000"')).toBeVisible(); // Max tokens

    // Check variant has correct border color (ai-primary)
    await expect(page.locator('[class*="border-ai-primary"]')).toBeVisible();
  });

  test('should handle multiple model selections up to max limit', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Select multiple models
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    const geminiCard = page.locator('[class*="card"]').filter({ hasText: 'Gemini Pro' });
    await geminiCard.locator('button:has-text("Add Variant")').click();

    const llamaCard = page.locator('[class*="card"]').filter({ hasText: 'Llama 2 7B' });
    await llamaCard.locator('button:has-text("Add Variant")').click();

    // Check variant count updates
    await expect(page.locator('text=Selected Model Variants (3/5)')).toBeVisible();

    // Check all three variants are visible
    const variantCards = page.locator('[class*="border-ai-primary"]');
    await expect(variantCards).toHaveCount(3);
  });

  test('should handle model variant removal', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Add a model
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    // Check variant is added
    await expect(page.locator('text=Selected Model Variants (1/5)')).toBeVisible();

    // Remove the variant
    const removeButton = page.locator('[class*="border-ai-primary"]').locator('button').filter({ hasText: '' }).nth(1); // X button
    await removeButton.click();

    // Check variant is removed
    await expect(page.locator('text=Selected Model Variants')).not.toBeVisible();
    await expect(page.locator('[class*="border-ai-primary"]')).not.toBeVisible();
  });

  test('should open and handle parameter editing dialog', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Add a model
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    // Click parameter edit button (tool icon)
    const editButton = page.locator('[class*="border-ai-primary"]').locator('button').filter({ hasText: '' }).first(); // Tool button
    await editButton.click();

    // Check parameter dialog opens
    await expect(page.locator('text=Configure Model Parameters')).toBeVisible();

    // Check parameter controls
    await expect(page.locator('text*="Temperature:"')).toBeVisible();
    await expect(page.locator('text*="Max Tokens:"')).toBeVisible();
    await expect(page.locator('text*="Top P:"')).toBeVisible();

    // Check sliders are present
    await expect(page.locator('[role="slider"]')).toHaveCount(3);

    // Check action buttons
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    await expect(page.locator('button:has-text("Save Parameters")')).toBeVisible();
  });

  test('should modify parameters and save changes', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Add a model and open parameter editor
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    const editButton = page.locator('[class*="border-ai-primary"]').locator('button').filter({ hasText: '' }).first();
    await editButton.click();

    // Modify temperature slider
    const temperatureSlider = page.locator('[role="slider"]').first();
    await temperatureSlider.click(); // This should change the value

    // Save parameters
    await page.locator('button:has-text("Save Parameters")').click();

    // Check dialog closes
    await expect(page.locator('text=Configure Model Parameters')).not.toBeVisible();

    // Check that parameter display in variant card might have updated
    await expect(page.locator('[class*="border-ai-primary"]')).toBeVisible();
  });

  test('should handle search functionality', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Search for "GPT"
    const searchInput = page.locator('input[placeholder="Search models..."]');
    await searchInput.fill('GPT');

    // Should show only GPT models
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).not.toBeVisible();
    await expect(page.locator('text=Gemini Pro')).not.toBeVisible();

    // Clear search
    await searchInput.fill('');

    // All models should be visible again
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
    await expect(page.locator('text=Gemini Pro')).toBeVisible();
  });

  test('should handle provider filtering', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click provider filter dropdown
    await page.locator('text=All Providers').click();

    // Select OpenAI
    await page.locator('text=OpenAI').nth(1).click(); // Second instance in dropdown

    // Should show only OpenAI models
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).not.toBeVisible();
    await expect(page.locator('text=Gemini Pro')).not.toBeVisible();

    // Reset filter
    await page.locator('text=OpenAI').click(); // Now shows selected provider
    await page.locator('text=All Providers').click();

    // All models should be visible again
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
  });

  test('should handle capability filtering', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click capability filter dropdown
    await page.locator('text=All Capabilities').click();

    // Select Vision capability
    await page.locator('text=Vision').click();

    // Should show only models with vision capability (Claude and Gemini)
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
    await expect(page.locator('text=Gemini Pro')).toBeVisible();
    await expect(page.locator('text=GPT-4')).not.toBeVisible(); // GPT-4 doesn't have vision in mock
    await expect(page.locator('text=Llama 2 7B')).not.toBeVisible();
  });

  test('should handle "Free Only" filter', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click "Free Only" filter
    await page.locator('button:has-text("Free Only")').click();

    // Should show only free models (Ollama models)
    await expect(page.locator('text=Llama 2 7B')).toBeVisible();
    await expect(page.locator('text=GPT-4')).not.toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).not.toBeVisible();
    await expect(page.locator('text=Gemini Pro')).not.toBeVisible();

    // Check button appears active
    await expect(page.locator('button:has-text("Free Only")[class*="default"]')).toBeVisible();
  });

  test('should handle "With Credentials" filter', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Click "With Credentials" filter
    await page.locator('button:has-text("With Credentials")').click();

    // Should show only models from providers with credentials (OpenAI and Gemini)
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Gemini Pro')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).not.toBeVisible(); // Anthropic has no credentials

    // Check button appears active with shield icon
    await expect(page.locator('button:has-text("With Credentials")[class*="default"]')).toBeVisible();
    await expect(page.locator('button:has-text("With Credentials") svg')).toBeVisible();
  });

  test('should switch between "By Provider" and "All Models" views', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Default to "By Provider" view
    await expect(page.locator('button[role="tab"]:has-text("By Provider")[aria-selected="true"]')).toBeVisible();
    await expect(page.locator('text=OpenAI')).toBeVisible();

    // Switch to "All Models" view
    await page.locator('button[role="tab"]:has-text("All Models")').click();

    // Should show all models in a flat list
    await expect(page.locator('button[role="tab"]:has-text("All Models")[aria-selected="true"]')).toBeVisible();
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
    
    // Provider section headers should not be visible in list view
    await expect(page.locator('text=OpenAI').and(page.locator('h3'))).not.toBeVisible();
  });

  test('should handle credentials requirement messaging', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Set up console logging to capture alert messages
    const alertMessages: string[] = [];
    page.on('dialog', dialog => {
      alertMessages.push(dialog.message());
      dialog.accept();
    });

    // Try to select Claude model (requires credentials but none set up)
    const claudeCard = page.locator('[class*="card"]').filter({ hasText: 'Claude 3 Opus' });
    await claudeCard.locator('button:has-text("Add Variant")').click();

    // Should show alert about credentials
    await page.waitForTimeout(100);
    expect(alertMessages).toContain('Please set up credentials for Anthropic first.');

    // Check that variant was not added
    await expect(page.locator('text=Selected Model Variants')).not.toBeVisible();
  });

  test('should handle loading and error states', async ({ page }) => {
    // Test loading state
    await page.route('**/api/v1/models/catalog', async route => {
      // Delay response to test loading state
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockModelCatalog)
      });
    });

    await page.goto('/stream');
    await page.locator('text=Show Settings').click();

    // Should show loading spinner
    await expect(page.locator('.animate-spin')).toBeVisible();

    // Wait for loading to complete
    await page.waitForTimeout(1500);
    await expect(page.locator('text=Model Browser')).toBeVisible();
  });

  test('should handle error state and retry', async ({ page }) => {
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

    // Wait for error to appear
    await page.waitForTimeout(1000);

    // Should show error message and retry button
    await expect(page.locator('text*="Failed to load"')).toBeVisible();
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();

    // Mock successful response for retry
    await page.route('**/api/v1/models/catalog', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockModelCatalog)
      });
    });

    // Click retry
    await page.locator('button:has-text("Retry")').click();

    // Should load successfully
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Model Browser')).toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Model browser should still be accessible
    await expect(page.locator('text=Model Browser')).toBeVisible();
    await expect(page.locator('input[placeholder="Search models..."]')).toBeVisible();

    // Filter buttons should be visible but may stack
    await expect(page.locator('button:has-text("Free Only")')).toBeVisible();
    await expect(page.locator('button:has-text("With Credentials")')).toBeVisible();

    // Model cards should stack in single column
    const modelCards = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await expect(modelCards).toBeVisible();

    // Add a model to test responsive variant display
    await modelCards.locator('button:has-text("Add Variant")').click();
    await expect(page.locator('text=Selected Model Variants')).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Test Tab navigation through search and filters
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Test search input focus
    const searchInput = page.locator('input[placeholder="Search models..."]');
    await searchInput.focus();
    await expect(searchInput).toBeFocused();

    // Test typing in search
    await page.keyboard.type('GPT');
    await expect(searchInput).toHaveValue('GPT');

    // Test tab navigation for view switching
    await page.locator('button[role="tab"]:has-text("By Provider")').focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('button[role="tab"]:has-text("All Models")').nth(0)).toBeFocused();

    // Test Enter to activate tab
    await page.keyboard.press('Enter');
    await expect(page.locator('button[role="tab"]:has-text("All Models")[aria-selected="true"]')).toBeVisible();
  });

  test('should handle accessibility requirements', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Check ARIA roles for tabs
    await expect(page.locator('button[role="tab"]')).toHaveCount(2);
    await expect(page.locator('[role="tabpanel"]')).toHaveCount(1);

    // Check form labels
    await expect(page.locator('label')).toHaveCount(0); // No visible labels in basic view

    // Add a model and check parameter dialog accessibility
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    const editButton = page.locator('[class*="border-ai-primary"]').locator('button').filter({ hasText: '' }).first();
    await editButton.click();

    // Check parameter dialog has proper labels
    await expect(page.locator('text*="Temperature:"')).toBeVisible();
    await expect(page.locator('text*="Max Tokens:"')).toBeVisible();
    await expect(page.locator('[role="slider"]')).toHaveCount(3);

    // Check dialog has proper title
    await expect(page.locator('text=Configure Model Parameters')).toBeVisible();
  });

  test('should persist selections when switching views', async ({ page }) => {
    await page.goto('/stream');
    await page.locator('text=Show Settings').click();
    await page.waitForTimeout(1000);

    // Add a model in "By Provider" view
    const gpt4Card = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await gpt4Card.locator('button:has-text("Add Variant")').click();

    // Check variant is selected
    await expect(page.locator('text=Selected Model Variants (1/5)')).toBeVisible();

    // Switch to "All Models" view
    await page.locator('button[role="tab"]:has-text("All Models")').click();

    // Selected variants should still be visible
    await expect(page.locator('text=Selected Model Variants (1/5)')).toBeVisible();

    // Model should show as selected in list view
    const gpt4CardInList = page.locator('[class*="card"]').filter({ hasText: 'GPT-4' });
    await expect(gpt4CardInList.locator('button:has-text("Selected")')).toBeVisible();

    // Switch back to "By Provider" view
    await page.locator('button[role="tab"]:has-text("By Provider")').click();

    // Selections should persist
    await expect(page.locator('text=Selected Model Variants (1/5)')).toBeVisible();
  });
});