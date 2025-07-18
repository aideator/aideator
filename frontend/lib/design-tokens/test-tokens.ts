/**
 * Design Tokens Test Suite
 * 
 * This file contains a small test suite to verify the token system works correctly.
 * It tests that tokens return exactly the same values as the current hardcoded implementations.
 * 
 * Phase 1: Validate that tokens work without changing existing components
 * Usage: Run this in the browser console or as a Node.js script
 */

import { validateDesignTokens, runValidationWithLogging } from './validation'
import { 
  getAgentColorClasses,
  getOutputTypeColorClasses,
  getStatusColorClasses,
  agentColors,
  outputTypeColors,
} from './colors'

/**
 * Test that agent color functions return expected values
 */
function testAgentColors(): boolean {
  console.group('🎨 Testing Agent Colors')
  
  let allPassed = true
  
  // Test each agent variation
  for (let i = 0; i <= 5; i++) {
    const expected = agentColors[i as keyof typeof agentColors]
    const actual = getAgentColorClasses(i)
    
    if (actual === expected) {
      console.log(`✅ Agent ${i}: ${actual}`)
    } else {
      console.error(`❌ Agent ${i}: expected "${expected}", got "${actual}"`)
      allPassed = false
    }
  }
  
  // Test fallback behavior
  const fallback = getAgentColorClasses(99)
  const expectedFallback = agentColors[0]
  if (fallback === expectedFallback) {
    console.log(`✅ Fallback: ${fallback}`)
  } else {
    console.error(`❌ Fallback: expected "${expectedFallback}", got "${fallback}"`)
    allPassed = false
  }
  
  console.groupEnd()
  return allPassed
}

/**
 * Test that output type color functions return expected values
 */
function testOutputTypeColors(): boolean {
  console.group('🏷️  Testing Output Type Colors')
  
  let allPassed = true
  
  // Test common output types
  const outputTypes = ['stdout', 'stderr', 'error', 'assistant_response', 'system_status', 'debug_info']
  
  for (const outputType of outputTypes) {
    const expected = outputTypeColors[outputType as keyof typeof outputTypeColors]
    const actual = getOutputTypeColorClasses(outputType)
    
    if (actual === expected) {
      console.log(`✅ ${outputType}: ${actual}`)
    } else {
      console.error(`❌ ${outputType}: expected "${expected}", got "${actual}"`)
      allPassed = false
    }
  }
  
  // Test fallback behavior
  const fallback = getOutputTypeColorClasses('unknown_type')
  const expectedFallback = outputTypeColors.stdout
  if (fallback === expectedFallback) {
    console.log(`✅ Fallback: ${fallback}`)
  } else {
    console.error(`❌ Fallback: expected "${expectedFallback}", got "${fallback}"`)
    allPassed = false
  }
  
  console.groupEnd()
  return allPassed
}

/**
 * Test that tokens match the original hardcoded values
 */
function testTokenCompatibility(): boolean {
  console.group('🔄 Testing Token Compatibility')
  
  let allPassed = true
  
  // Original hardcoded agentColors from agent-output-viewer.tsx
  const originalAgentColors = {
    0: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
    1: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
    2: 'border-amber-500/20 bg-amber-50 dark:bg-amber-950/20',
    3: 'border-rose-500/20 bg-rose-50 dark:bg-rose-950/20',
    4: 'border-emerald-500/20 bg-emerald-50 dark:bg-emerald-950/20',
    5: 'border-indigo-500/20 bg-indigo-50 dark:bg-indigo-950/20',
  }
  
  // Original hardcoded outputTypeColors from agent-output-viewer.tsx
  const originalOutputTypeColors = {
    stdout: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    stderr: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    assistant_response: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
    system_status: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    debug_info: 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400',
  }
  
  // Test agent colors compatibility
  for (let i = 0; i <= 5; i++) {
    const originalValue = originalAgentColors[i as keyof typeof originalAgentColors]
    const tokenValue = agentColors[i as keyof typeof agentColors]
    
    if (originalValue === tokenValue) {
      console.log(`✅ Agent color ${i} matches original`)
    } else {
      console.error(`❌ Agent color ${i} mismatch: original="${originalValue}", token="${tokenValue}"`)
      allPassed = false
    }
  }
  
  // Test output type colors compatibility
  for (const [key, originalValue] of Object.entries(originalOutputTypeColors)) {
    const tokenValue = outputTypeColors[key as keyof typeof outputTypeColors]
    
    if (originalValue === tokenValue) {
      console.log(`✅ Output type ${key} matches original`)
    } else {
      console.error(`❌ Output type ${key} mismatch: original="${originalValue}", token="${tokenValue}"`)
      allPassed = false
    }
  }
  
  console.groupEnd()
  return allPassed
}

/**
 * Test that helper functions work correctly
 */
function testHelperFunctions(): boolean {
  console.group('🛠️  Testing Helper Functions')
  
  let allPassed = true
  
  // Test getAgentColorClasses with various inputs
  const agentTests = [
    { input: 0, expected: agentColors[0] },
    { input: 1, expected: agentColors[1] },
    { input: 5, expected: agentColors[5] },
    { input: -1, expected: agentColors[0] }, // Should fallback to 0
    { input: 999, expected: agentColors[0] }, // Should fallback to 0
  ]
  
  for (const test of agentTests) {
    const actual = getAgentColorClasses(test.input)
    if (actual === test.expected) {
      console.log(`✅ getAgentColorClasses(${test.input}) = ${actual}`)
    } else {
      console.error(`❌ getAgentColorClasses(${test.input}): expected "${test.expected}", got "${actual}"`)
      allPassed = false
    }
  }
  
  // Test getOutputTypeColorClasses with various inputs
  const outputTests = [
    { input: 'stdout', expected: outputTypeColors.stdout },
    { input: 'stderr', expected: outputTypeColors.stderr },
    { input: 'error', expected: outputTypeColors.error },
    { input: 'unknown', expected: outputTypeColors.stdout }, // Should fallback to stdout
    { input: '', expected: outputTypeColors.stdout }, // Should fallback to stdout
  ]
  
  for (const test of outputTests) {
    const actual = getOutputTypeColorClasses(test.input)
    if (actual === test.expected) {
      console.log(`✅ getOutputTypeColorClasses('${test.input}') = ${actual}`)
    } else {
      console.error(`❌ getOutputTypeColorClasses('${test.input}'): expected "${test.expected}", got "${actual}"`)
      allPassed = false
    }
  }
  
  console.groupEnd()
  return allPassed
}

/**
 * Main test runner
 */
export function runDesignTokenTests(): boolean {
  console.group('🧪 Design Token Test Suite')
  console.log('Running comprehensive tests for design tokens...')
  
  const agentColorsPassed = testAgentColors()
  const outputTypeColorsPassed = testOutputTypeColors()
  const compatibilityPassed = testTokenCompatibility()
  const helpersPassed = testHelperFunctions()
  
  const allPassed = agentColorsPassed && outputTypeColorsPassed && compatibilityPassed && helpersPassed
  
  console.log('\n' + '='.repeat(50))
  if (allPassed) {
    console.log('🎉 All tests passed! Design tokens are working correctly.')
  } else {
    console.error('❌ Some tests failed. Please review the issues above.')
  }
  console.log('='.repeat(50))
  
  console.groupEnd()
  
  return allPassed
}

/**
 * Run validation tests as well
 */
export function runAllTests(): boolean {
  console.log('🚀 Running all design token tests and validation...')
  
  const testsPassed = runDesignTokenTests()
  
  console.log('\n' + '='.repeat(50))
  console.log('📋 Running validation...')
  runValidationWithLogging()
  
  return testsPassed
}

/**
 * Quick smoke test for development
 */
export function quickTest(): void {
  console.log('🔥 Quick smoke test...')
  
  // Test a few critical functions
  const agent0 = getAgentColorClasses(0)
  const stdout = getOutputTypeColorClasses('stdout')
  const error = getOutputTypeColorClasses('error')
  
  console.log('Agent 0:', agent0)
  console.log('Stdout:', stdout)
  console.log('Error:', error)
  
  // Verify they're not empty
  if (agent0 && stdout && error) {
    console.log('✅ Quick test passed!')
  } else {
    console.error('❌ Quick test failed!')
  }
}

// Auto-run tests if this file is executed directly
if (typeof window !== 'undefined' && window.console) {
  // Browser environment
  console.log('🌐 Design tokens loaded in browser')
  console.log('Run runAllTests() to test the design token system')
} else if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
  // Test environment
  runAllTests()
}

// Export for use in other files
export default {
  runDesignTokenTests,
  runAllTests,
  quickTest,
  testAgentColors,
  testOutputTypeColors,
  testTokenCompatibility,
  testHelperFunctions,
}