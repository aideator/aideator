import { test, expect } from '@playwright/test';

test.describe('Model Catalog E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the stream page
    await page.goto('http://localhost:3000/stream');
  });

  test('should display model selector with LiteLLM canonical names', async ({ page }) => {
    // Wait for the model selector to be visible
    await page.waitForSelector('[data-testid="model-selector"]', { timeout: 10000 });
    
    // Click on model selector to open dropdown
    await page.click('[data-testid="model-selector"]');
    
    // Check that canonical model names are displayed
    await expect(page.locator('text=GPT-4')).toBeVisible();
    await expect(page.locator('text=GPT-3.5 Turbo')).toBeVisible();
    
    // Check for Claude models with version numbers
    await expect(page.locator('text=Claude 3 Opus')).toBeVisible();
    await expect(page.locator('text=Claude 3 Sonnet')).toBeVisible();
    
    // Check for Gemini models
    await expect(page.locator('text=Gemini Pro')).toBeVisible();
  });

  test('should allow selecting multiple models', async ({ page }) => {
    // Click on model selector
    await page.click('[data-testid="model-selector"]');
    
    // Select GPT-4
    await page.click('text=GPT-4');
    
    // Select Claude
    await page.click('text=Claude 3 Opus');
    
    // Check that both models are selected
    const selectedModels = await page.locator('[data-testid="selected-models"]').textContent();
    expect(selectedModels).toContain('2 models selected');
  });

  test('should send correct model names to API', async ({ page }) => {
    // Set up API request interception
    const apiRequests: any[] = [];
    await page.route('**/api/v1/runs', async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        const postData = request.postDataJSON();
        apiRequests.push(postData);
      }
      await route.continue();
    });
    
    // Select models
    await page.click('[data-testid="model-selector"]');
    await page.click('text=GPT-4');
    await page.click('text=Claude 3 Opus');
    
    // Enter a prompt
    await page.fill('[data-testid="prompt-input"]', 'Test prompt');
    
    // Click generate
    await page.click('[data-testid="generate-button"]');
    
    // Wait for API call
    await page.waitForTimeout(1000);
    
    // Check that API was called with correct model names
    expect(apiRequests.length).toBeGreaterThan(0);
    const request = apiRequests[0];
    
    // Check model variants have correct model_definition_id
    expect(request.model_variants).toBeDefined();
    const modelIds = request.model_variants.map((v: any) => v.model_definition_id);
    
    // Should use canonical LiteLLM names
    expect(modelIds).toContain('gpt-4');
    expect(modelIds).toContain('claude-3-opus-20240229');
  });

  test('should handle models without API keys gracefully', async ({ page }) => {
    // Try to generate with a model that requires missing API key
    await page.click('[data-testid="model-selector"]');
    
    // Look for models that might not have API keys configured
    const modelElements = await page.locator('[data-testid^="model-option-"]').all();
    
    // Select a model
    if (modelElements.length > 0) {
      await modelElements[0].click();
    }
    
    // Enter prompt and generate
    await page.fill('[data-testid="prompt-input"]', 'Test prompt');
    await page.click('[data-testid="generate-button"]');
    
    // Should show error if API key is missing
    // (This depends on which models have API keys configured)
    const errorMessage = await page.locator('[data-testid="error-message"]').textContent();
    if (errorMessage) {
      expect(errorMessage).toMatch(/API key|not available|configured/i);
    }
  });
});