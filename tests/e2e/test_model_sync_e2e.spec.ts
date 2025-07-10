import { test, expect } from '@playwright/test';

test.describe('Model Sync E2E Tests', () => {
  // Admin user credentials for testing
  const adminEmail = 'admin@aideator.com';
  const adminPassword = 'AdminPass123!';
  let adminApiKey: string;

  test.beforeAll(async ({ request }) => {
    // Register admin user if not exists
    try {
      await request.post('http://localhost:8000/api/v1/auth/register', {
        data: {
          username: 'admin',
          email: adminEmail,
          password: adminPassword
        }
      });
    } catch {
      // User might already exist
    }

    // Login to get token
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        email: adminEmail,
        password: adminPassword
      }
    });
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.access_token;

    // Create API key
    const apiKeyResponse = await request.post('http://localhost:8000/api/v1/auth/api-keys', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      data: {
        name: 'Admin Test Key',
        description: 'For E2E testing'
      }
    });
    expect(apiKeyResponse.ok()).toBeTruthy();
    const apiKeyData = await apiKeyResponse.json();
    adminApiKey = apiKeyData.key;
  });

  test('should trigger model sync as admin', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/admin/models/sync', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.message).toContain('triggered');
  });

  test('should get sync history', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/admin/models/sync/history', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    
    // If there are sync logs, verify structure
    if (data.length > 0) {
      const syncLog = data[0];
      expect(syncLog).toHaveProperty('status');
      expect(syncLog).toHaveProperty('started_at');
      expect(syncLog).toHaveProperty('models_discovered');
    }
  });

  test('should get sync status', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/admin/models/sync/status', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('sync_task_running');
    expect(data).toHaveProperty('active_models_count');
    expect(data).toHaveProperty('sync_interval_minutes');
  });

  test('should reject non-admin access to sync endpoints', async ({ request }) => {
    // Create regular user
    const regularEmail = 'user@example.com';
    const regularPassword = 'UserPass123!';

    await request.post('http://localhost:8000/api/v1/auth/register', {
      data: {
        username: 'regularuser',
        email: regularEmail,
        password: regularPassword
      }
    });

    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        email: regularEmail,
        password: regularPassword
      }
    });
    const loginData = await loginResponse.json();
    const token = loginData.access_token;

    const apiKeyResponse = await request.post('http://localhost:8000/api/v1/auth/api-keys', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      data: {
        name: 'User Test Key'
      }
    });
    const apiKeyData = await apiKeyResponse.json();
    const userApiKey = apiKeyData.key;

    // Try to access admin endpoints
    const syncResponse = await request.post('http://localhost:8000/api/v1/admin/models/sync', {
      headers: {
        'X-API-Key': userApiKey
      }
    });

    expect(syncResponse.status()).toBe(403);
    const errorData = await syncResponse.json();
    expect(errorData.detail).toContain('Admin privileges required');
  });

  test('should load models from database after sync', async ({ request }) => {
    // Trigger a sync first
    await request.post('http://localhost:8000/api/v1/admin/models/sync', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });

    // Wait a bit for sync to complete
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Get models from catalog
    const response = await request.get('http://localhost:8000/api/v1/models/catalog', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.models).toBeDefined();
    expect(Array.isArray(data.models)).toBeTruthy();
    
    // Verify model structure if any exist
    if (data.models.length > 0) {
      const model = data.models[0];
      expect(model).toHaveProperty('model_name');
      expect(model).toHaveProperty('litellm_model_name');
      expect(model).toHaveProperty('display_name');
      expect(model).toHaveProperty('provider');
      expect(model).toHaveProperty('capabilities');
    }
  });

  test('should update model catalog on frontend after sync', async ({ page, request }) => {
    // Navigate to stream page
    await page.goto('http://localhost:3000/stream');
    
    // Wait for model selector
    await page.waitForSelector('[data-testid="model-selector"]', { timeout: 10000 });
    
    // Trigger backend sync
    await request.post('http://localhost:8000/api/v1/admin/models/sync', {
      headers: {
        'X-API-Key': adminApiKey
      }
    });
    
    // Wait for sync
    await page.waitForTimeout(2000);
    
    // Refresh page to get updated models
    await page.reload();
    
    // Open model selector
    await page.click('[data-testid="model-selector"]');
    
    // Check that models are displayed
    await expect(page.locator('text=OpenAI')).toBeVisible({ timeout: 5000 });
    
    // Verify we can see model options
    const modelOptions = await page.locator('[data-testid^="model-option-"]').all();
    expect(modelOptions.length).toBeGreaterThan(0);
  });
});