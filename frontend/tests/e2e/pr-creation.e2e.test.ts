import { test, expect } from '@playwright/test'

test.describe('PR Creation E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'test-token')
      window.localStorage.setItem('user', JSON.stringify({
        id: 'test-user',
        name: 'Test User',
        email: 'test@example.com'
      }))
    })
  })

  test('should create PR successfully with valid data', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    await page.route('**/api/v1/tasks/123/variations/0/pull-request', async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          pr_url: 'https://github.com/test/repo/pull/123'
        })
      })
    })

    // Navigate to task page
    await page.goto('/task/123')
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="task-page"]', { timeout: 10000 })
    
    // Click on Create PR tab
    await page.click('text=Create PR')
    
    // Wait for PR creation form to load
    await page.waitForSelector('text=Create Pull Request')
    
    // Verify form elements are present
    await expect(page.locator('text=PR Title')).toBeVisible()
    await expect(page.locator('text=PR Description')).toBeVisible()
    await expect(page.locator('text=Files to be changed')).toBeVisible()
    await expect(page.locator('text=Preview Changes')).toBeVisible()
    
    // Verify default values
    await expect(page.locator('input[value="AIdeator – Task 123 Variation 1"]')).toBeVisible()
    await expect(page.locator('textarea')).toContainText('Test summary')
    
    // Verify repository information
    await expect(page.locator('text=Repository:')).toBeVisible()
    await expect(page.locator('text=https://github.com/test/repo')).toBeVisible()
    
    // Verify file changes
    await expect(page.locator('text=test.py')).toBeVisible()
    await expect(page.locator('text=+5')).toBeVisible()
    await expect(page.locator('text=-2')).toBeVisible()
    
    // Verify ready state
    await expect(page.locator('text=Ready to create PR:')).toBeVisible()
    await expect(page.locator('text=• GitHub repository: test/repo')).toBeVisible()
    await expect(page.locator('text=• 1 file modified')).toBeVisible()
    
    // Create PR
    await page.click('button:has-text("Create Pull Request")')
    
    // Wait for success state
    await page.waitForSelector('text=Pull Request Created')
    
    // Verify success elements
    await expect(page.locator('text=Pull Request Created')).toBeVisible()
    await expect(page.locator('text=Your pull request has been successfully created on GitHub')).toBeVisible()
    await expect(page.locator('text=Ready to Review')).toBeVisible()
    await expect(page.locator('button:has-text("View on GitHub")')).toBeVisible()
    
    // Click view PR button (should open in new tab)
    const [newPage] = await Promise.all([
      page.context().waitForEvent('page'),
      page.click('button:has-text("View on GitHub")')
    ])
    
    // Verify new page opened
    expect(newPage.url()).toBe('https://github.com/test/repo/pull/123')
  })

  test('should handle validation errors', async ({ page }) => {
    // Mock task data without GitHub URL
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: '', // No GitHub URL
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: []
            }]
          }
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Verify requirements not met message
    await expect(page.locator('text=Requirements not met:')).toBeVisible()
    await expect(page.locator('text=• No GitHub repository associated with this task')).toBeVisible()
    
    // Verify button is disabled
    await expect(page.locator('button:has-text("Create Pull Request")')).toBeDisabled()
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    // Mock PR creation to fail
    await page.route('**/api/v1/tasks/123/variations/0/pull-request', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Access denied'
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Create PR
    await page.click('button:has-text("Create Pull Request")')
    
    // Verify error message
    await expect(page.locator('text=Access denied. Please check your repository permissions.')).toBeVisible()
  })

  test('should handle rate limiting with retry', async ({ page }) => {
    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    let requestCount = 0
    await page.route('**/api/v1/tasks/123/variations/0/pull-request', async route => {
      requestCount++
      if (requestCount === 1) {
        // First request: rate limit
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Rate limit exceeded'
          })
        })
      } else {
        // Second request: success
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            pr_url: 'https://github.com/test/repo/pull/123'
          })
        })
      }
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Create PR
    await page.click('button:has-text("Create Pull Request")')
    
    // Should show retrying message
    await expect(page.locator('text=Retrying... (1/3)')).toBeVisible()
    
    // Should eventually succeed
    await page.waitForSelector('text=Pull Request Created', { timeout: 10000 })
    await expect(page.locator('text=Pull Request Created')).toBeVisible()
  })

  test('should validate form inputs', async ({ page }) => {
    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Test title validation
    const titleInput = page.locator('input[value="AIdeator – Task 123 Variation 1"]')
    await titleInput.clear()
    await titleInput.fill('Hi')
    
    // Should show validation error
    await expect(page.locator('text=PR title must be at least 5 characters')).toBeVisible()
    
    // Button should be disabled
    await expect(page.locator('button:has-text("Create Pull Request")')).toBeDisabled()
    
    // Fix title
    await titleInput.clear()
    await titleInput.fill('Valid Title')
    
    // Error should disappear
    await expect(page.locator('text=PR title must be at least 5 characters')).not.toBeVisible()
    
    // Button should be enabled
    await expect(page.locator('button:has-text("Create Pull Request")')).toBeEnabled()
  })

  test('should handle keyboard navigation', async ({ page }) => {
    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Test tab navigation
    await page.keyboard.press('Tab')
    await expect(page.locator('input[value="AIdeator – Task 123 Variation 1"]')).toBeFocused()
    
    await page.keyboard.press('Tab')
    await expect(page.locator('textarea')).toBeFocused()
    
    await page.keyboard.press('Tab')
    await expect(page.locator('button:has-text("Create Pull Request")')).toBeFocused()
  })

  test('should show character count for inputs', async ({ page }) => {
    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Verify character counts are displayed
    await expect(page.locator('text=25/100 characters')).toBeVisible()
    await expect(page.locator('text=12/2000 characters')).toBeVisible()
    
    // Update title and verify count updates
    const titleInput = page.locator('input[value="AIdeator – Task 123 Variation 1"]')
    await titleInput.clear()
    await titleInput.fill('New Title')
    
    await expect(page.locator('text=9/100 characters')).toBeVisible()
  })

  test('should handle authentication errors', async ({ page }) => {
    // Clear authentication
    await page.addInitScript(() => {
      window.localStorage.removeItem('auth_token')
      window.localStorage.removeItem('user')
    })

    // Mock task data
    await page.route('**/api/v1/tasks/123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '123',
          title: 'Test Task',
          details: 'Test task details',
          status: 'Completed',
          versions: 1,
          github_url: 'https://github.com/test/repo',
          taskDetails: {
            versions: [{
              id: 1,
              summary: 'Test summary',
              files: [{
                name: 'test.py',
                additions: 5,
                deletions: 2
              }]
            }]
          }
        })
      })
    })

    await page.goto('/task/123')
    await page.click('text=Create PR')
    
    // Verify authentication error
    await expect(page.locator('text=Please log in with GitHub to create pull requests')).toBeVisible()
    
    // Button should be disabled
    await expect(page.locator('button:has-text("Create Pull Request")')).toBeDisabled()
  })
})