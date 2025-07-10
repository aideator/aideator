import { test, expect } from '@playwright/test';

test.describe('Agent Streaming - Comprehensive E2E Tests', () => {
  
  const testRunId = 'test-stream-run-12345';

  // Mock streaming data for multiple agents
  const mockStreamingEvents = [
    // Agent 0 events
    { event: 'agent_output', data: { variation_id: 0, content: 'Starting code analysis...', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_output', data: { variation_id: 0, content: '\n\nAnalyzing repository structure...', timestamp: '2024-01-15T10:00:01Z' }},
    { event: 'agent_output', data: { variation_id: 0, content: '\n\nFound 47 files in the repository:', timestamp: '2024-01-15T10:00:02Z' }},
    { event: 'agent_output', data: { variation_id: 0, content: '\n- main.py\n- requirements.txt\n- README.md', timestamp: '2024-01-15T10:00:03Z' }},
    
    // Agent 1 events
    { event: 'agent_output', data: { variation_id: 1, content: 'Initializing security scan...', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_output', data: { variation_id: 1, content: '\n\nScanning for vulnerabilities...', timestamp: '2024-01-15T10:00:01Z' }},
    { event: 'agent_output', data: { variation_id: 1, content: '\n\n✅ No security issues found', timestamp: '2024-01-15T10:00:02Z' }},
    
    // Agent 2 events
    { event: 'agent_output', data: { variation_id: 2, content: 'Reviewing code quality...', timestamp: '2024-01-15T10:00:00Z' }},
    { event: 'agent_output', data: { variation_id: 2, content: '\n\nAnalyzing patterns and best practices...', timestamp: '2024-01-15T10:00:01Z' }},
    { event: 'agent_output', data: { variation_id: 2, content: '\n\n## Code Quality Report\n\n- Maintainability: Good\n- Readability: Excellent', timestamp: '2024-01-15T10:00:02Z' }},
    
    // Completion events
    { event: 'agent_complete', data: { variation_id: 0, status: 'completed' }},
    { event: 'agent_complete', data: { variation_id: 1, status: 'completed' }},
    { event: 'agent_complete', data: { variation_id: 2, status: 'completed' }},
    { event: 'run_complete', data: { run_id: testRunId, status: 'completed' }}
  ];

  test.beforeEach(async ({ page }) => {
    // Mock run creation API
    await page.route('**/api/v1/runs', async route => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          runId: testRunId,
          sessionId: 'test-session-123',
          turnId: 'test-turn-123'
        })
      });
    });

    // Mock auth endpoints for clean testing
    await page.route('**/api/v1/auth/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: false,
          user: null
        })
      });
    });
  });

  test('should initialize streaming interface correctly', async ({ page }) => {
    await page.goto('/stream');

    // Check initial streaming interface elements
    await expect(page.locator('h1')).toContainText('aideator');
    await expect(page.locator('text=Multi-Model Prompt Comparison Platform')).toBeVisible();
    
    // Check input area
    await expect(page.locator('textarea[placeholder*="Ask a question"]')).toBeVisible();
    
    // Check settings toggle
    await expect(page.locator('text=Show Settings')).toBeVisible();
  });

  test('should display stream grid with multiple agent cards', async ({ page }) => {
    // Mock streaming endpoint with multiple agents
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    // Submit a prompt to start streaming
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Analyze this codebase comprehensively');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Wait for stream to start
    await page.waitForTimeout(1000);

    // Check that multiple agent cards are visible
    await expect(page.locator('text=gpt-4o-mini 1')).toBeVisible();
    await expect(page.locator('text=gpt-4o-mini 2')).toBeVisible();
    await expect(page.locator('text=gpt-4o-mini 3')).toBeVisible();

    // Check streaming indicators
    await expect(page.locator('text=Thinking...')).toHaveCount(3);
    await expect(page.locator('.animate-spin')).toHaveCount(3); // Spinner icons
  });

  test('should display real-time content streaming in agent cards', async ({ page }) => {
    // Mock progressive streaming
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      // Simulate slower streaming for testing
      let sseData = '';
      const firstFewEvents = mockStreamingEvents.slice(0, 6); // First 6 events
      
      firstFewEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Perform code analysis');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check content appears in agent cards
    await expect(page.locator('text=Starting code analysis...')).toBeVisible();
    await expect(page.locator('text=Initializing security scan...')).toBeVisible();
    await expect(page.locator('text=Reviewing code quality...')).toBeVisible();

    // Check content accumulates over time
    await expect(page.locator('text=Analyzing repository structure...')).toBeVisible();
    await expect(page.locator('text=Scanning for vulnerabilities...')).toBeVisible();
  });

  test('should handle agent status transitions correctly', async ({ page }) => {
    // Mock streaming with completion events
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Complete analysis');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Check completion status appears
    await expect(page.locator('text=Complete')).toHaveCount(3);
    
    // Check completion icons (CheckCircle)
    const completedCards = page.locator('[class*="bg-red-500"], [class*="bg-amber-500"], [class*="bg-emerald-500"]'); // Agent color headers
    await expect(completedCards).toHaveCount(3);
  });

  test('should show connection status indicators', async ({ page }) => {
    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test connection status');
    
    await page.locator('text=Show Settings').click();

    // Mock connecting state
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      // Delay to simulate connecting state
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'event: status\ndata: {"status": "connecting"}\n\n'
      });
    });
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    // Should show connecting status
    await expect(page.locator('text=Connecting...')).toBeVisible();
    
    // Check connection icon
    await expect(page.locator('svg').filter({ hasText: '' })).toBeVisible(); // Wifi icon
  });

  test('should handle streaming errors gracefully', async ({ page }) => {
    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test error handling');
    
    await page.locator('text=Show Settings').click();

    // Mock error response
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Connection failed' })
      });
    });
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Should show error state
    await expect(page.locator('text=Connection Error')).toBeVisible();
    
    // Check error icon
    await expect(page.locator('svg').filter({ hasText: '' })).toBeVisible(); // WifiOff icon
  });

  test('should enable agent selection after completion', async ({ page }) => {
    // Mock streaming with completion
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    // Mock selection API
    await page.route('**/api/v1/runs/*/select', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test agent selection');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Check selection buttons are enabled
    const selectionButtons = page.locator('button:has-text("I prefer this response")');
    await expect(selectionButtons).toHaveCount(3);
    
    // Click first agent selection
    await selectionButtons.first().click();
    
    // Should handle selection (would need to check backend integration)
    await page.waitForTimeout(500);
  });

  test('should handle auto-scrolling behavior in agent cards', async ({ page }) => {
    // Mock long streaming content
    const longStreamingEvents = [
      { event: 'agent_output', data: { variation_id: 0, content: 'Line 1: Starting analysis...', timestamp: '2024-01-15T10:00:00Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\nLine 2: Processing files...', timestamp: '2024-01-15T10:00:01Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\nLine 3: Analyzing patterns...', timestamp: '2024-01-15T10:00:02Z' }},
    ];

    for (let i = 4; i <= 20; i++) {
      longStreamingEvents.push({
        event: 'agent_output',
        data: { 
          variation_id: 0, 
          content: `\nLine ${i}: Additional analysis content line ${i}...`,
          timestamp: `2024-01-15T10:00:${String(i-1).padStart(2, '0')}Z`
        }
      });
    }

    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      longStreamingEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Generate long output for scroll testing');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1500);

    // Check that content is scrollable
    const contentArea = page.locator('.overflow-y-auto').first();
    await expect(contentArea).toBeVisible();
    
    // Check that multiple lines are present
    await expect(page.locator('text=Line 1:')).toBeVisible();
    await expect(page.locator('text=Line 20:')).toBeVisible();
  });

  test('should display message and character counts', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      const events = mockStreamingEvents.slice(0, 4); // First few events for agent 0
      let sseData = '';
      events.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test message counting');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check message count display
    await expect(page.locator('text*="messages"')).toBeVisible();
    
    // Check character count display
    await expect(page.locator('text*="chars"')).toBeVisible();
  });

  test('should handle responsive layout on different screen sizes', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.slice(0, 9).forEach(event => { // 3 agents worth of events
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');

    // Test desktop layout
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test responsive layout');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Should show 3 columns on desktop
    await expect(page.locator('text=gpt-4o-mini 1')).toBeVisible();
    await expect(page.locator('text=gpt-4o-mini 2')).toBeVisible();
    await expect(page.locator('text=gpt-4o-mini 3')).toBeVisible();

    // Test tablet layout
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('text=gpt-4o-mini 1')).toBeVisible();

    // Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('text=gpt-4o-mini 1')).toBeVisible();
    
    // Cards should stack vertically on mobile
    const agentCards = page.locator('[class*="bg-white"][class*="rounded-xl"]');
    await expect(agentCards.first()).toBeVisible();
  });

  test('should handle debug functionality in agent cards', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.slice(0, 4).forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test debug functionality');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check debug buttons are present (if debug mode is enabled)
    // This would depend on environment configuration
    const debugButtons = page.locator('[class*="debug"]');
    if (await debugButtons.count() > 0) {
      await expect(debugButtons.first()).toBeVisible();
    }
  });

  test('should handle keyboard navigation in streaming interface', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.slice(0, 6).forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');

    // Test Tab navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Focus on prompt input
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.focus();
    await expect(promptInput).toBeFocused();

    // Type prompt
    await page.keyboard.type('Test keyboard navigation');

    // Navigate to settings
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Open settings

    // Navigate to send button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Send

    await page.waitForTimeout(1000);

    // After streaming starts, test navigation through agent cards
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to reach selection buttons
    const selectionButtons = page.locator('button:has-text("I prefer this response")');
    if (await selectionButtons.count() > 0) {
      await selectionButtons.first().focus();
      await expect(selectionButtons.first()).toBeFocused();
    }
  });

  test('should handle concurrent streaming from multiple agents', async ({ page }) => {
    // Mock interleaved streaming from multiple agents
    const interleavedEvents = [
      { event: 'agent_output', data: { variation_id: 0, content: 'Agent 0: Starting...', timestamp: '2024-01-15T10:00:00Z' }},
      { event: 'agent_output', data: { variation_id: 1, content: 'Agent 1: Initializing...', timestamp: '2024-01-15T10:00:00Z' }},
      { event: 'agent_output', data: { variation_id: 2, content: 'Agent 2: Beginning...', timestamp: '2024-01-15T10:00:00Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\nAgent 0: Continuing...', timestamp: '2024-01-15T10:00:01Z' }},
      { event: 'agent_output', data: { variation_id: 1, content: '\nAgent 1: Processing...', timestamp: '2024-01-15T10:00:01Z' }},
      { event: 'agent_output', data: { variation_id: 2, content: '\nAgent 2: Analyzing...', timestamp: '2024-01-15T10:00:01Z' }},
    ];

    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      interleavedEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test concurrent streaming');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check all agents have content
    await expect(page.locator('text=Agent 0: Starting...')).toBeVisible();
    await expect(page.locator('text=Agent 1: Initializing...')).toBeVisible();
    await expect(page.locator('text=Agent 2: Beginning...')).toBeVisible();

    // Check content continues for all agents
    await expect(page.locator('text=Agent 0: Continuing...')).toBeVisible();
    await expect(page.locator('text=Agent 1: Processing...')).toBeVisible();
    await expect(page.locator('text=Agent 2: Analyzing...')).toBeVisible();

    // Check active status indicator
    await expect(page.locator('text*="3 / 5 Active"')).toBeVisible();
  });

  test('should handle markdown rendering in agent outputs', async ({ page }) => {
    const markdownEvents = [
      { event: 'agent_output', data: { variation_id: 0, content: '# Code Analysis Report', timestamp: '2024-01-15T10:00:00Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\n\n## Overview\n\nThis is a **comprehensive** analysis.', timestamp: '2024-01-15T10:00:01Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\n\n```python\ndef hello():\n    print("Hello, World!")\n```', timestamp: '2024-01-15T10:00:02Z' }},
      { event: 'agent_output', data: { variation_id: 0, content: '\n\n- Item 1\n- Item 2\n- Item 3', timestamp: '2024-01-15T10:00:03Z' }},
    ];

    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      markdownEvents.forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Generate markdown report');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check markdown is rendered (headings, formatting, code blocks, lists)
    await expect(page.locator('h1')).toHaveCount(2); // Page title + rendered H1
    await expect(page.locator('h2')).toBeVisible(); // Overview heading
    await expect(page.locator('strong')).toBeVisible(); // Bold text
    await expect(page.locator('code')).toBeVisible(); // Code blocks
    await expect(page.locator('ul')).toBeVisible(); // Lists
  });

  test('should handle accessibility requirements for streaming interface', async ({ page }) => {
    await page.route(`**/api/v1/runs/${testRunId}/stream`, async route => {
      let sseData = '';
      mockStreamingEvents.slice(0, 6).forEach(event => {
        sseData += `event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`;
      });
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: sseData
      });
    });

    await page.goto('/stream');
    
    const promptInput = page.locator('textarea[placeholder*="Ask a question"]');
    await promptInput.fill('Test accessibility');
    
    await page.locator('text=Show Settings').click();
    
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).locator('[data-testid="play-icon"], .lucide-play');
    await sendButton.click();

    await page.waitForTimeout(1000);

    // Check ARIA labels and roles
    await expect(page.locator('button[role="button"]')).toHaveCount(4); // Selection buttons + send button

    // Check heading hierarchy
    const headings = page.locator('h1, h2, h3, h4');
    await expect(headings).toHaveCount(4); // Page title + 3 agent titles

    // Check focus indicators work
    const firstSelectionButton = page.locator('button:has-text("I prefer this response")').first();
    await firstSelectionButton.focus();
    await expect(firstSelectionButton).toBeFocused();

    // Check color contrast for streaming status indicators
    await expect(page.locator('text=Thinking...')).toHaveCSS('color', /rgb/);
    
    // Check that all interactive elements are keyboard accessible
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    // Should be able to navigate through all interactive elements
  });
});