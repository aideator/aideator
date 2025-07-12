import { test, expect } from '@playwright/test'

test.describe('Basic Application', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')
    
    // Check that the main heading is visible
    await expect(page.locator('h1')).toContainText('What are we coding next?')
    
    // Check that the textarea is present
    await expect(page.locator('textarea')).toBeVisible()
    
    // Check that the repository selector is present
    await expect(page.locator('text=aideator/helloworld')).toBeVisible()
  })

  test('can type in task textarea', async ({ page }) => {
    await page.goto('/')
    
    const textarea = page.locator('textarea')
    await textarea.fill('Test task description')
    
    await expect(textarea).toHaveValue('Test task description')
    
    // Check that buttons appear when there's text
    await expect(page.locator('text=Ask')).toBeVisible()
    await expect(page.locator('text=Code')).toBeVisible()
  })
})