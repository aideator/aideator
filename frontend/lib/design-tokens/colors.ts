/**
 * Color Design Tokens
 * 
 * This file contains the color palette and color functions used throughout the AIdeator frontend.
 * All colors are designed to work with Tailwind CSS v3.4.17 and enforce complete class names.
 * 
 * Phase 1: Extract existing color patterns to establish baseline
 * Phase 2: These tokens will be gradually adopted by components
 */

/**
 * Agent Color System
 * 
 * Used for visual differentiation between agent variations in the output viewer.
 * Each agent gets a unique color scheme for cards, borders, and backgrounds.
 * Colors match the original hardcoded values with stronger borders for visibility.
 */
export const agentColors = {
  0: 'border-cyan-500/40 bg-cyan-50 dark:bg-cyan-950/20',
  1: 'border-cyan-500/40 bg-cyan-50 dark:bg-cyan-950/20',
  2: 'border-violet-500/40 bg-violet-50 dark:bg-violet-950/20',
  3: 'border-orange-500/40 bg-orange-50 dark:bg-orange-950/20',
  4: 'border-rose-500/40 bg-rose-50 dark:bg-rose-950/20',
  5: 'border-emerald-500/40 bg-emerald-50 dark:bg-emerald-950/20',
  6: 'border-blue-500/40 bg-blue-50 dark:bg-blue-950/20',
} as const

/**
 * Output Type Color System
 * 
 * Used for color-coding different types of agent output (stdout, stderr, etc.).
 * Each output type gets distinct colors for badges and text.
 * Colors match the original hardcoded values with colored backgrounds and borders.
 */
export const outputTypeColors = {
  stdout: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  stderr: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  status: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  summary: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  logging: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  diffs: 'border-yellow-500/40 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  addinfo: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  job_data: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
  error: 'border-red-500/40 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  assistant_response: 'border-green-500/40 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  system_status: 'border-blue-500/40 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  debug_info: 'border-purple-500/40 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
} as const

/**
 * Status Color System
 * 
 * Used for task status indicators, loading states, and error states.
 */
export const statusColors = {
  open: 'text-green-400 bg-green-900/50',
  completed: 'text-green-400',
  failed: 'text-red-400',
  processing: 'text-blue-400',
  error: 'text-red-500',
  loading: 'text-blue-500',
  success: 'text-green-500',
} as const

/**
 * UI Element Color System
 * 
 * Common color patterns used across various UI elements.
 */
export const uiColors = {
  primary: {
    background: 'bg-gray-950',
    text: 'text-gray-50',
    border: 'border-gray-800',
  },
  secondary: {
    background: 'bg-gray-900',
    text: 'text-gray-200',
    border: 'border-gray-700',
  },
  accent: {
    background: 'bg-white',
    text: 'text-black',
    hover: 'hover:bg-gray-200',
  },
  muted: {
    background: 'bg-gray-800/60',
    text: 'text-gray-400',
    border: 'border-gray-700',
  },
  highlight: {
    hover: 'hover:bg-gray-900 hover:bg-gray-800/50',
    focus: 'focus:bg-gray-700',
  },
} as const

/**
 * Type definitions for better TypeScript support
 */
export type AgentVariationId = keyof typeof agentColors
export type OutputType = keyof typeof outputTypeColors
export type StatusType = keyof typeof statusColors

/**
 * Helper function to get agent color classes
 * Returns the exact same classes as the current hardcoded agentColors object
 * Maps variation IDs to match original hardcoded sequence
 */
export function getAgentColorClasses(variationId: number): string {
  // Map 0-indexed variation IDs to 1-indexed color keys (0-5 maps to keys 1-6, fallback to 0)
  const colorKey = (variationId >= 0 && variationId <= 5) ? variationId + 1 : 0
  return agentColors[colorKey as AgentVariationId] || agentColors[0]
}

/**
 * Helper function to get output type color classes
 * Returns the exact same classes as the current hardcoded outputTypeColors object
 * Falls back to a default gray style for unknown types
 */
export function getOutputTypeColorClasses(outputType: string): string {
  return outputTypeColors[outputType as OutputType] || 'border-gray-500/40 bg-gray-100 dark:bg-gray-800/50 text-gray-700 dark:text-gray-400'
}

/**
 * Helper function to get status color classes
 */
export function getStatusColorClasses(status: string): string {
  return statusColors[status as StatusType] || statusColors.error
}

/**
 * Validation function to ensure colors are properly defined
 * This helps catch missing color definitions during development
 */
export function validateColorTokens(): {
  valid: boolean
  issues: string[]
} {
  const issues: string[] = []
  
  // Check that all agent colors are defined
  const maxAgentVariations = 6
  for (let i = 0; i <= maxAgentVariations; i++) {
    if (!agentColors[i as AgentVariationId]) {
      issues.push(`Agent color missing for variation ${i}`)
    }
  }
  
  // Check that all output type colors contain expected classes
  const requiredOutputTypes = ['stdout', 'stderr', 'error', 'assistant_response', 'system_status', 'debug_info', 'diffs']
  for (const outputType of requiredOutputTypes) {
    if (!outputTypeColors[outputType as OutputType]) {
      issues.push(`Output type color missing for ${outputType}`)
    }
  }
  
  return {
    valid: issues.length === 0,
    issues
  }
}