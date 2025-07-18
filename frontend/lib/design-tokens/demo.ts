/**
 * Design Tokens Demo
 * 
 * This file demonstrates how the design token system works and shows
 * that it returns exactly the same values as the current hardcoded implementations.
 * 
 * Phase 1: Proof of concept that tokens work without breaking existing functionality
 * Usage: Import and run in a React component or browser console
 */

import {
  getAgentColorClasses,
  getOutputTypeColorClasses,
  getStatusColorClasses,
  getHeadingClasses,
  getBodyClasses,
  getCodeClasses,
  getContainerSpacing,
  getGapSpacing,
  combineDesignTokens,
  componentTokens,
  themeUtils,
  runAllTests,
  quickTest,
} from './index'

/**
 * Demonstrate agent color system
 */
export function demoAgentColors() {
  console.group('🎨 Agent Color System Demo')
  
  console.log('Agent variation colors:')
  for (let i = 0; i <= 5; i++) {
    const classes = getAgentColorClasses(i)
    console.log(`  Agent ${i}: ${classes}`)
  }
  
  console.log('\nFallback behavior:')
  console.log(`  Agent 99: ${getAgentColorClasses(99)}`)
  console.log(`  Agent -1: ${getAgentColorClasses(-1)}`)
  
  console.groupEnd()
}

/**
 * Demonstrate output type color system
 */
export function demoOutputTypeColors() {
  console.group('🏷️  Output Type Color System Demo')
  
  const outputTypes = [
    'stdout', 'stderr', 'error', 'assistant_response', 
    'system_status', 'debug_info', 'diffs', 'summary'
  ]
  
  console.log('Output type colors:')
  for (const outputType of outputTypes) {
    const classes = getOutputTypeColorClasses(outputType)
    console.log(`  ${outputType}: ${classes}`)
  }
  
  console.log('\nFallback behavior:')
  console.log(`  unknown_type: ${getOutputTypeColorClasses('unknown_type')}`)
  
  console.groupEnd()
}

/**
 * Demonstrate typography system
 */
export function demoTypography() {
  console.group('📝 Typography System Demo')
  
  console.log('Heading styles:')
  console.log(`  Page title: ${getHeadingClasses('h1', 'primary')}`)
  console.log(`  Section header: ${getHeadingClasses('h2', 'section')}`)
  console.log(`  Card title: ${getHeadingClasses('h2', 'card')}`)
  
  console.log('\nBody styles:')
  console.log(`  Primary text: ${getBodyClasses('primary')}`)
  console.log(`  Secondary text: ${getBodyClasses('secondary')}`)
  console.log(`  Detail text: ${getBodyClasses('detail')}`)
  
  console.log('\nCode styles:')
  console.log(`  Inline code: ${getCodeClasses('inline')}`)
  console.log(`  Code block: ${getCodeClasses('block')}`)
  console.log(`  Log output: ${getCodeClasses('log')}`)
  
  console.groupEnd()
}

/**
 * Demonstrate spacing system
 */
export function demoSpacing() {
  console.group('📐 Spacing System Demo')
  
  console.log('Container spacing:')
  console.log(`  Page layout: ${getContainerSpacing('page')}`)
  console.log(`  Card content: ${getContainerSpacing('card')}`)
  console.log(`  Header: ${getContainerSpacing('header')}`)
  
  console.log('\nGap spacing:')
  console.log(`  Small gap: ${getGapSpacing('sm')}`)
  console.log(`  Medium gap: ${getGapSpacing('md')}`)
  console.log(`  Button group: ${getGapSpacing('buttons')}`)
  
  console.groupEnd()
}

/**
 * Demonstrate component token combinations
 */
export function demoComponentTokens() {
  console.group('🧩 Component Token Combinations Demo')
  
  console.log('Agent output viewer:')
  console.log(`  Variation 0 card: ${componentTokens.agentOutput.getVariationCardClasses(0)}`)
  console.log(`  Variation 1 card: ${componentTokens.agentOutput.getVariationCardClasses(1)}`)
  console.log(`  Stdout output: ${componentTokens.agentOutput.getOutputLineClasses('stdout')}`)
  console.log(`  Error output: ${componentTokens.agentOutput.getOutputLineClasses('error')}`)
  
  console.log('\nTask status:')
  console.log(`  Open task: ${componentTokens.task.getStatusClasses('open')}`)
  console.log(`  Completed task: ${componentTokens.task.getStatusClasses('completed')}`)
  console.log(`  Failed task: ${componentTokens.task.getStatusClasses('failed')}`)
  
  console.log('\nUI elements:')
  console.log(`  Primary button: ${componentTokens.ui.button.primary}`)
  console.log(`  Secondary button: ${componentTokens.ui.button.secondary}`)
  console.log(`  Primary card: ${componentTokens.ui.card.primary}`)
  console.log(`  Page layout: ${componentTokens.ui.layout.page}`)
  
  console.groupEnd()
}

/**
 * Demonstrate token combination utility
 */
export function demoTokenCombination() {
  console.group('🔗 Token Combination Demo')
  
  // Combine multiple tokens
  const agentCardClasses = combineDesignTokens(
    getAgentColorClasses(0),
    getContainerSpacing('card'),
    'rounded-lg border'
  )
  
  const outputBadgeClasses = combineDesignTokens(
    getOutputTypeColorClasses('error'),
    getCodeClasses('inline'),
    'rounded px-2 py-1'
  )
  
  const pageLayoutClasses = combineDesignTokens(
    getContainerSpacing('page'),
    getBodyClasses('primary'),
    themeUtils.themes.background.primary
  )
  
  console.log('Combined token examples:')
  console.log(`  Agent card: ${agentCardClasses}`)
  console.log(`  Output badge: ${outputBadgeClasses}`)
  console.log(`  Page layout: ${pageLayoutClasses}`)
  
  console.groupEnd()
}

/**
 * Demonstrate compatibility with existing hardcoded values
 */
export function demoCompatibility() {
  console.group('🔄 Compatibility Demo')
  
  // Show that tokens return exact same values as hardcoded objects
  console.log('Compatibility with agent-output-viewer.tsx:')
  
  const originalAgentColors = {
    0: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
    1: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
    2: 'border-amber-500/20 bg-amber-50 dark:bg-amber-950/20',
  }
  
  const originalOutputTypeColors = {
    stdout: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    stderr: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  }
  
  // Compare original vs token values
  console.log('Agent color comparison:')
  Object.entries(originalAgentColors).forEach(([key, originalValue]) => {
    const tokenValue = getAgentColorClasses(Number(key))
    const matches = originalValue === tokenValue
    console.log(`  Agent ${key}: ${matches ? '✅' : '❌'} ${matches ? 'matches' : 'differs'}`)
    if (!matches) {
      console.log(`    Original: ${originalValue}`)
      console.log(`    Token:    ${tokenValue}`)
    }
  })
  
  console.log('\nOutput type color comparison:')
  Object.entries(originalOutputTypeColors).forEach(([key, originalValue]) => {
    const tokenValue = getOutputTypeColorClasses(key)
    const matches = originalValue === tokenValue
    console.log(`  ${key}: ${matches ? '✅' : '❌'} ${matches ? 'matches' : 'differs'}`)
    if (!matches) {
      console.log(`    Original: ${originalValue}`)
      console.log(`    Token:    ${tokenValue}`)
    }
  })
  
  console.groupEnd()
}

/**
 * Run all demos
 */
export function runAllDemos() {
  console.group('🚀 Design Token System Demo')
  console.log('Demonstrating the Phase 1 design token system...')
  
  demoAgentColors()
  demoOutputTypeColors()
  demoTypography()
  demoSpacing()
  demoComponentTokens()
  demoTokenCombination()
  demoCompatibility()
  
  console.log('\n' + '='.repeat(50))
  console.log('🎉 Demo complete! The design token system is working correctly.')
  console.log('💡 Next steps: Gradually adopt tokens in components during Phase 2.')
  console.log('='.repeat(50))
  
  console.groupEnd()
}

/**
 * Quick demo for development
 */
export function quickDemo() {
  console.log('🔥 Quick demo of design tokens...')
  
  const agent0 = getAgentColorClasses(0)
  const stdout = getOutputTypeColorClasses('stdout')
  const error = getOutputTypeColorClasses('error')
  const cardTitle = getHeadingClasses('h2', 'card')
  const pageLayout = getContainerSpacing('page')
  
  console.log(`Agent 0: ${agent0}`)
  console.log(`Stdout: ${stdout}`)
  console.log(`Error: ${error}`)
  console.log(`Card title: ${cardTitle}`)
  console.log(`Page layout: ${pageLayout}`)
  
  console.log('✅ Quick demo complete!')
}

/**
 * Run demo with tests
 */
export function runDemoWithTests() {
  console.log('🎯 Running demo with validation tests...')
  
  runAllDemos()
  
  console.log('\n' + '='.repeat(50))
  console.log('Running validation tests...')
  runAllTests()
}

// Auto-run demo if this file is executed directly
if (typeof window !== 'undefined' && window.console) {
  console.log('🌐 Design token demo loaded!')
  console.log('Run runAllDemos() to see the complete demo')
  console.log('Run quickDemo() for a quick test')
}

// Export for use in other files
export default {
  runAllDemos,
  quickDemo,
  runDemoWithTests,
  demoAgentColors,
  demoOutputTypeColors,
  demoTypography,
  demoSpacing,
  demoComponentTokens,
  demoTokenCombination,
  demoCompatibility,
}