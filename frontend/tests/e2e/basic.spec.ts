import { test, expect } from '@playwright/test'

test.describe('Basic Application', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')
    
    // Check that the main heading is visible
    await expect(page.locator('h1')).toContainText('What are we chatting about today?')
    
    // Check that the textarea is present
    await expect(page.locator('textarea')).toBeVisible()
    
    // Check that the page has loaded correctly
    await expect(page.locator('.bg-gray-950')).toBeVisible()
  })

  test('can type in task textarea', async ({ page }) => {
    await page.goto('/')
    
    const textarea = page.locator('textarea')
    await textarea.fill('Test task description')
    
    await expect(textarea).toHaveValue('Test task description')
    
    // Check that the text was entered correctly
    const textareaValue = await textarea.inputValue()
    expect(textareaValue).toBe('Test task description')
  })
})