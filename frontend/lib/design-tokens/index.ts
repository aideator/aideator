/**
 * Design Tokens - Main Entry Point
 * 
 * This file serves as the main entry point for the AIdeator design token system.
 * It exports all tokens and provides utility functions for working with them.
 * 
 * Phase 1: Foundational infrastructure without breaking existing functionality
 * Phase 2: Gradual adoption by components
 */

// Export all color tokens
export {
  agentColors,
  outputTypeColors,
  statusColors,
  uiColors,
  getAgentColorClasses,
  getOutputTypeColorClasses,
  getStatusColorClasses,
  validateColorTokens,
  type AgentVariationId,
  type OutputType,
  type StatusType,
} from './colors'

// Export all typography tokens
export {
  headingTypography,
  bodyTypography,
  codeTypography,
  interactiveTypography,
  statusTypography,
  badgeTypography,
  commonTypographyCombinations,
  getHeadingClasses,
  getBodyClasses,
  getCodeClasses,
  getInteractiveClasses,
  getStatusClasses,
  getBadgeClasses,
  validateTypographyTokens,
  type HeadingLevel,
  type HeadingVariant,
  type BodyVariant,
  type CodeVariant,
  type InteractiveVariant,
  type StatusVariant,
  type BadgeVariant,
} from './typography'

// Export all spacing tokens
export {
  containerSpacing,
  gapSpacing,
  marginSpacing,
  paddingSpacing,
  layoutSpacing,
  componentSpacing,
  commonSpacingCombinations,
  getContainerSpacing,
  getGapSpacing,
  getMarginSpacing,
  getPaddingSpacing,
  getLayoutSpacing,
  getComponentSpacing,
  validateSpacingTokens,
  type ContainerSpacingVariant,
  type GapSpacingVariant,
  type MarginSpacingVariant,
  type PaddingSpacingVariant,
  type LayoutSpacingVariant,
} from './spacing'

// Export validation and testing utilities
export {
  validateDesignTokens,
  runValidationWithLogging,
  validateAgentColorHelpers,
  validateOutputTypeColorHelpers,
  validateTypographyHelpers,
  validateSpacingHelpers,
  validateTokenCompleteness,
  validateTailwindClasses,
} from './validation'

export {
  runDesignTokenTests,
  runAllTests,
  quickTest,
} from './test-tokens'

/**
 * Master validation function to check all design tokens
 */
export function validateAllDesignTokens(): {
  valid: boolean
  issues: string[]
} {
  // Import validation functions from individual modules
  const { validateColorTokens } = require('./colors')
  const { validateTypographyTokens } = require('./typography')
  const { validateSpacingTokens } = require('./spacing')
  
  const colorValidation = validateColorTokens()
  const typographyValidation = validateTypographyTokens()
  const spacingValidation = validateSpacingTokens()
  
  const allIssues = [
    ...colorValidation.issues,
    ...typographyValidation.issues,
    ...spacingValidation.issues,
  ]
  
  return {
    valid: allIssues.length === 0,
    issues: allIssues
  }
}

/**
 * Utility function to combine multiple design token classes
 * This helps ensure consistent class ordering and prevents conflicts
 */
export function combineDesignTokens(...tokens: (string | undefined | null)[]): string {
  return tokens
    .filter(Boolean)
    .join(' ')
    .trim()
}

/**
 * Theme-aware utility functions
 * These functions help with theme switching and dark mode support
 */
export const themeUtils = {
  /**
   * Get theme-appropriate classes based on current theme
   */
  getThemeClasses: (lightClasses: string, darkClasses: string) => {
    return `${lightClasses} ${darkClasses}`
  },
  
  /**
   * Common theme combinations used throughout the app
   */
  themes: {
    background: {
      primary: 'bg-gray-950',
      secondary: 'bg-gray-900',
      card: 'bg-gray-900/80',
      hover: 'hover:bg-gray-900 dark:hover:bg-gray-800/50',
    },
    text: {
      primary: 'text-gray-50',
      secondary: 'text-gray-200',
      muted: 'text-gray-400',
      accent: 'text-gray-300 hover:text-gray-50',
    },
    border: {
      primary: 'border-gray-800',
      secondary: 'border-gray-700',
    },
  },
}

/**
 * Component-specific token combinations
 * These are common patterns that combine multiple token types
 */
export const componentTokens = {
  /**
   * Agent output viewer tokens
   */
  agentOutput: {
    getVariationCardClasses: (variationId: number) => {
      const { getAgentColorClasses } = require('./colors')
      return combineDesignTokens(
        'h-full',
        getAgentColorClasses(variationId)
      )
    },
    
    getOutputLineClasses: (outputType: string) => {
      const { getOutputTypeColorClasses } = require('./colors')
      return combineDesignTokens(
        'text-xs font-mono',
        getOutputTypeColorClasses(outputType)
      )
    },
  },
  
  /**
   * Task page tokens
   */
  task: {
    getStatusClasses: (status: string) => {
      const { getStatusColorClasses } = require('./colors')
      return combineDesignTokens(
        'text-sm px-2 py-1 rounded-md',
        getStatusColorClasses(status)
      )
    },
  },
  
  /**
   * Common UI element tokens
   */
  ui: {
    button: {
      primary: combineDesignTokens(
        'bg-white text-black hover:bg-gray-200'
      ),
      secondary: combineDesignTokens(
        'bg-gray-800 border-gray-700'
      ),
      ghost: combineDesignTokens(
        'text-gray-300 hover:text-gray-50'
      ),
    },
    
    card: {
      primary: combineDesignTokens(
        'bg-gray-900/80 border border-gray-800 rounded-xl p-4'
      ),
      secondary: combineDesignTokens(
        'bg-gray-800/60 border-gray-700'
      ),
    },
    
    layout: {
      page: combineDesignTokens(
        'bg-gray-950 text-gray-50 min-h-screen'
      ),
      container: combineDesignTokens(
        'container mx-auto max-w-3xl py-16'
      ),
      header: combineDesignTokens(
        'border-b border-gray-800 bg-gray-950'
      ),
    },
  },
}

/**
 * Development utilities
 * These functions help with development and debugging
 */
export const devUtils = {
  /**
   * Log all design tokens to console (development only)
   */
  logTokens: () => {
    if (process.env.NODE_ENV === 'development') {
      const { agentColors, outputTypeColors, statusColors } = require('./colors')
      const { headingTypography, bodyTypography, codeTypography } = require('./typography')
      const { containerSpacing, gapSpacing, marginSpacing } = require('./spacing')
      
      console.group('🎨 Design Tokens')
      console.log('Colors:', { agentColors, outputTypeColors, statusColors })
      console.log('Typography:', { headingTypography, bodyTypography, codeTypography })
      console.log('Spacing:', { containerSpacing, gapSpacing, marginSpacing })
      console.groupEnd()
    }
  },
  
  /**
   * Check if a token exists
   */
  hasToken: (tokenPath: string): boolean => {
    try {
      const { agentColors, outputTypeColors } = require('./colors')
      const { headingTypography } = require('./typography')
      const { containerSpacing } = require('./spacing')
      
      const parts = tokenPath.split('.')
      let current: any = { agentColors, outputTypeColors, headingTypography, containerSpacing }
      
      for (const part of parts) {
        if (current[part] === undefined) {
          return false
        }
        current = current[part]
      }
      
      return true
    } catch {
      return false
    }
  },
  
  /**
   * Get token value by path
   */
  getToken: (tokenPath: string): string | undefined => {
    try {
      const { agentColors, outputTypeColors } = require('./colors')
      const { headingTypography } = require('./typography')
      const { containerSpacing } = require('./spacing')
      
      const parts = tokenPath.split('.')
      let current: any = { agentColors, outputTypeColors, headingTypography, containerSpacing }
      
      for (const part of parts) {
        if (current[part] === undefined) {
          return undefined
        }
        current = current[part]
      }
      
      return typeof current === 'string' ? current : undefined
    } catch {
      return undefined
    }
  },
}

/**
 * Version information
 */
export const designTokensVersion = '1.0.0-phase1'
export const designTokensPhase = 'Phase 1: Foundational Infrastructure'

/**
 * Default export for convenience
 */
export default {
  version: designTokensVersion,
  phase: designTokensPhase,
  validate: validateAllDesignTokens,
  combine: combineDesignTokens,
  components: componentTokens,
  theme: themeUtils,
  dev: devUtils,
}