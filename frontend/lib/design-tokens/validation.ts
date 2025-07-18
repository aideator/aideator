/**
 * Design Tokens Validation Framework
 * 
 * This file provides comprehensive validation for all design tokens
 * to ensure they return expected values and maintain consistency.
 * 
 * Phase 1: Establish baseline validation to prevent regressions
 * Phase 2: Extend validation as tokens are adopted by components
 */

import {
  agentColors,
  outputTypeColors,
  statusColors,
  getAgentColorClasses,
  getOutputTypeColorClasses,
  getStatusColorClasses,
} from './colors'

import {
  headingTypography,
  bodyTypography,
  codeTypography,
  commonTypographyCombinations,
  getHeadingClasses,
  getBodyClasses,
  getCodeClasses,
} from './typography'

import {
  containerSpacing,
  gapSpacing,
  marginSpacing,
  paddingSpacing,
  commonSpacingCombinations,
  getContainerSpacing,
  getGapSpacing,
  getMarginSpacing,
  getPaddingSpacing,
} from './spacing'

/**
 * Validation result interface
 */
interface ValidationResult {
  valid: boolean
  issues: string[]
  warnings: string[]
}

/**
 * Expected values for critical tokens
 * These are the exact values that should be returned by helper functions
 */
const expectedTokenValues = {
  agentColors: {
    0: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
    1: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
    2: 'border-amber-500/20 bg-amber-50 dark:bg-amber-950/20',
    3: 'border-rose-500/20 bg-rose-50 dark:bg-rose-950/20',
    4: 'border-emerald-500/20 bg-emerald-50 dark:bg-emerald-950/20',
    5: 'border-indigo-500/20 bg-indigo-50 dark:bg-indigo-950/20',
  },
  outputTypeColors: {
    stdout: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    stderr: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    assistant_response: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
    system_status: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    debug_info: 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400',
  },
  commonTypography: {
    pageTitle: 'text-4xl font-medium text-center',
    sectionHeader: 'text-lg font-semibold',
    cardTitle: 'text-sm font-medium',
    bodyText: 'text-gray-300',
    codeBlock: 'font-mono text-sm whitespace-pre-wrap',
  },
  commonSpacing: {
    pageLayout: 'container mx-auto max-w-3xl py-16',
    cardLayout: 'p-4 space-y-4',
    buttonGroup: 'flex items-center gap-2',
    listItem: 'py-2 px-3',
  },
} as const

/**
 * Validate that agent color helper functions return expected values
 */
function validateAgentColorHelpers(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Test each agent variation
  for (let i = 0; i <= 5; i++) {
    const expected = expectedTokenValues.agentColors[i as keyof typeof expectedTokenValues.agentColors]
    const actual = getAgentColorClasses(i)
    
    if (actual !== expected) {
      issues.push(`Agent color ${i}: expected "${expected}", got "${actual}"`)
    }
  }
  
  // Test fallback behavior
  const fallbackResult = getAgentColorClasses(99)
  const expectedFallback = expectedTokenValues.agentColors[0]
  if (fallbackResult !== expectedFallback) {
    issues.push(`Agent color fallback: expected "${expectedFallback}", got "${fallbackResult}"`)
  }
  
  // Test negative values
  const negativeResult = getAgentColorClasses(-1)
  if (negativeResult !== expectedFallback) {
    issues.push(`Agent color negative: expected "${expectedFallback}", got "${negativeResult}"`)
  }
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Validate that output type color helper functions return expected values
 */
function validateOutputTypeColorHelpers(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Test each output type
  const outputTypes = ['stdout', 'stderr', 'error', 'assistant_response', 'system_status', 'debug_info']
  
  for (const outputType of outputTypes) {
    const expected = expectedTokenValues.outputTypeColors[outputType as keyof typeof expectedTokenValues.outputTypeColors]
    const actual = getOutputTypeColorClasses(outputType)
    
    if (actual !== expected) {
      issues.push(`Output type ${outputType}: expected "${expected}", got "${actual}"`)
    }
  }
  
  // Test fallback behavior
  const fallbackResult = getOutputTypeColorClasses('unknown_type')
  const expectedFallback = expectedTokenValues.outputTypeColors.stdout
  if (fallbackResult !== expectedFallback) {
    issues.push(`Output type fallback: expected "${expectedFallback}", got "${fallbackResult}"`)
  }
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Validate that typography helper functions return expected values
 */
function validateTypographyHelpers(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Test common typography combinations
  const typographyTests = [
    { key: 'pageTitle', expected: expectedTokenValues.commonTypography.pageTitle },
    { key: 'sectionHeader', expected: expectedTokenValues.commonTypography.sectionHeader },
    { key: 'cardTitle', expected: expectedTokenValues.commonTypography.cardTitle },
    { key: 'bodyText', expected: expectedTokenValues.commonTypography.bodyText },
    { key: 'codeBlock', expected: expectedTokenValues.commonTypography.codeBlock },
  ]
  
  for (const test of typographyTests) {
    const actual = commonTypographyCombinations[test.key as keyof typeof commonTypographyCombinations]
    if (actual !== test.expected) {
      issues.push(`Typography ${test.key}: expected "${test.expected}", got "${actual}"`)
    }
  }
  
  // Test specific helper functions
  const headingTest = getHeadingClasses('h1', 'primary')
  const expectedHeading = headingTypography.h1.primary
  if (headingTest !== expectedHeading) {
    issues.push(`Heading helper: expected "${expectedHeading}", got "${headingTest}"`)
  }
  
  const bodyTest = getBodyClasses('primary')
  const expectedBody = bodyTypography.primary
  if (bodyTest !== expectedBody) {
    issues.push(`Body helper: expected "${expectedBody}", got "${bodyTest}"`)
  }
  
  const codeTest = getCodeClasses('block')
  const expectedCode = codeTypography.block
  if (codeTest !== expectedCode) {
    issues.push(`Code helper: expected "${expectedCode}", got "${codeTest}"`)
  }
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Validate that spacing helper functions return expected values
 */
function validateSpacingHelpers(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Test common spacing combinations
  const spacingTests = [
    { key: 'pageLayout', expected: expectedTokenValues.commonSpacing.pageLayout },
    { key: 'cardLayout', expected: expectedTokenValues.commonSpacing.cardLayout },
    { key: 'buttonGroup', expected: expectedTokenValues.commonSpacing.buttonGroup },
    { key: 'listItem', expected: expectedTokenValues.commonSpacing.listItem },
  ]
  
  for (const test of spacingTests) {
    const actual = commonSpacingCombinations[test.key as keyof typeof commonSpacingCombinations]
    if (actual !== test.expected) {
      issues.push(`Spacing ${test.key}: expected "${test.expected}", got "${actual}"`)
    }
  }
  
  // Test specific helper functions
  const containerTest = getContainerSpacing('page')
  const expectedContainer = containerSpacing.page
  if (containerTest !== expectedContainer) {
    issues.push(`Container spacing helper: expected "${expectedContainer}", got "${containerTest}"`)
  }
  
  const gapTest = getGapSpacing('md')
  const expectedGap = gapSpacing.md
  if (gapTest !== expectedGap) {
    issues.push(`Gap spacing helper: expected "${expectedGap}", got "${gapTest}"`)
  }
  
  const marginTest = getMarginSpacing('sm')
  const expectedMargin = marginSpacing.sm
  if (marginTest !== expectedMargin) {
    issues.push(`Margin spacing helper: expected "${expectedMargin}", got "${marginTest}"`)
  }
  
  const paddingTest = getPaddingSpacing('md')
  const expectedPadding = paddingSpacing.md
  if (paddingTest !== expectedPadding) {
    issues.push(`Padding spacing helper: expected "${expectedPadding}", got "${paddingTest}"`)
  }
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Validate that all token objects have expected properties
 */
function validateTokenCompleteness(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Check agent colors completeness
  const requiredAgentColors = [0, 1, 2, 3, 4, 5]
  for (const colorId of requiredAgentColors) {
    if (!agentColors[colorId as keyof typeof agentColors]) {
      issues.push(`Missing agent color for variation ${colorId}`)
    }
  }
  
  // Check output type colors completeness
  const requiredOutputTypes = ['stdout', 'stderr', 'error', 'assistant_response', 'system_status', 'debug_info']
  for (const outputType of requiredOutputTypes) {
    if (!outputTypeColors[outputType as keyof typeof outputTypeColors]) {
      issues.push(`Missing output type color for ${outputType}`)
    }
  }
  
  // Check for empty or undefined values
  Object.entries(agentColors).forEach(([key, value]) => {
    if (!value || value.trim() === '') {
      issues.push(`Empty agent color value for ${key}`)
    }
  })
  
  Object.entries(outputTypeColors).forEach(([key, value]) => {
    if (!value || value.trim() === '') {
      issues.push(`Empty output type color value for ${key}`)
    }
  })
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Validate that token values contain only valid Tailwind classes
 */
function validateTailwindClasses(): ValidationResult {
  const issues: string[] = []
  const warnings: string[] = []
  
  // Common Tailwind class patterns
  const validClassPatterns = [
    /^(bg|text|border|hover|dark|focus|active|disabled|group|peer)-/,
    /^(p|m|px|py|mx|my|pt|pb|pl|pr|mt|mb|ml|mr)-/,
    /^(w|h|max-w|max-h|min-w|min-h)-/,
    /^(flex|grid|block|inline|hidden|visible)-/,
    /^(rounded|shadow|opacity|z)-/,
    /^(space|gap|justify|items|self|place)-/,
    /^(text|font|leading|tracking|whitespace)-/,
    /^(container|mx-auto|sr-only|not-sr-only)$/,
  ]
  
  function isValidTailwindClass(className: string): boolean {
    return validClassPatterns.some(pattern => pattern.test(className))
  }
  
  // Check agent colors
  Object.entries(agentColors).forEach(([key, value]) => {
    const classes = value.split(' ')
    classes.forEach(className => {
      if (className && !isValidTailwindClass(className)) {
        warnings.push(`Potentially invalid Tailwind class in agent color ${key}: "${className}"`)
      }
    })
  })
  
  // Check output type colors
  Object.entries(outputTypeColors).forEach(([key, value]) => {
    const classes = value.split(' ')
    classes.forEach(className => {
      if (className && !isValidTailwindClass(className)) {
        warnings.push(`Potentially invalid Tailwind class in output type ${key}: "${className}"`)
      }
    })
  })
  
  return {
    valid: issues.length === 0,
    issues,
    warnings,
  }
}

/**
 * Run all validation tests
 */
export function validateDesignTokens(): ValidationResult {
  const agentColorValidation = validateAgentColorHelpers()
  const outputTypeValidation = validateOutputTypeColorHelpers()
  const typographyValidation = validateTypographyHelpers()
  const spacingValidation = validateSpacingHelpers()
  const completenessValidation = validateTokenCompleteness()
  const tailwindValidation = validateTailwindClasses()
  
  const allIssues = [
    ...agentColorValidation.issues,
    ...outputTypeValidation.issues,
    ...typographyValidation.issues,
    ...spacingValidation.issues,
    ...completenessValidation.issues,
    ...tailwindValidation.issues,
  ]
  
  const allWarnings = [
    ...agentColorValidation.warnings,
    ...outputTypeValidation.warnings,
    ...typographyValidation.warnings,
    ...spacingValidation.warnings,
    ...completenessValidation.warnings,
    ...tailwindValidation.warnings,
  ]
  
  return {
    valid: allIssues.length === 0,
    issues: allIssues,
    warnings: allWarnings,
  }
}

/**
 * Run validation and log results to console
 */
export function runValidationWithLogging(): void {
  const result = validateDesignTokens()
  
  console.group('🧪 Design Token Validation Results')
  
  if (result.valid) {
    console.log('✅ All design tokens are valid!')
  } else {
    console.error('❌ Design token validation failed')
    console.group('Issues:')
    result.issues.forEach(issue => console.error(`  • ${issue}`))
    console.groupEnd()
  }
  
  if (result.warnings.length > 0) {
    console.group('⚠️  Warnings:')
    result.warnings.forEach(warning => console.warn(`  • ${warning}`))
    console.groupEnd()
  }
  
  console.log(`Total issues: ${result.issues.length}`)
  console.log(`Total warnings: ${result.warnings.length}`)
  
  console.groupEnd()
}

/**
 * Export individual validation functions for testing
 */
export {
  validateAgentColorHelpers,
  validateOutputTypeColorHelpers,
  validateTypographyHelpers,
  validateSpacingHelpers,
  validateTokenCompleteness,
  validateTailwindClasses,
}