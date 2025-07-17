/**
 * Typography Design Tokens
 * 
 * This file contains typography patterns extracted from existing components.
 * All typography classes are designed to work with Tailwind CSS v3.4.17.
 * 
 * Phase 1: Extract existing typography patterns to establish baseline
 * Phase 2: These tokens will be gradually adopted by components
 */

/**
 * Heading Typography System
 * 
 * Typography patterns for headings across the application.
 */
export const headingTypography = {
  h1: {
    primary: 'text-4xl font-medium text-center',
    page: 'text-lg font-semibold',
    task: 'text-lg font-medium text-gray-50',
    brand: 'text-xl font-semibold text-gray-50',
  },
  h2: {
    section: 'text-lg font-semibold',
    card: 'text-sm font-medium',
  },
  h3: {
    sidebar: 'font-semibold text-gray-400',
    error: 'font-medium text-red-300',
  },
  h4: {
    error: 'font-medium text-red-300',
    warning: 'font-medium text-orange-300',
  },
} as const

/**
 * Body Typography System
 * 
 * Typography patterns for body text, descriptions, and content.
 */
export const bodyTypography = {
  primary: 'text-gray-300',
  secondary: 'text-gray-400',
  muted: 'text-gray-500',
  detail: 'text-gray-400 text-sm',
  description: 'text-sm text-gray-400',
  content: 'text-sm',
  large: 'text-lg',
  center: 'text-center',
} as const

/**
 * Code Typography System
 * 
 * Typography patterns for code, logs, and monospace content.
 */
export const codeTypography = {
  inline: 'font-mono text-xs',
  block: 'font-mono text-sm',
  log: 'font-mono text-sm whitespace-pre-wrap',
  timestamp: 'text-xs text-gray-500 font-mono',
  diff: 'font-mono text-xs',
  badge: 'text-xs font-mono',
  file: 'font-mono text-xs',
} as const

/**
 * Interactive Typography System
 * 
 * Typography patterns for interactive elements like buttons and links.
 */
export const interactiveTypography = {
  button: {
    primary: 'text-black',
    secondary: 'text-gray-300',
    ghost: 'text-gray-300 hover:text-gray-50',
    tab: 'text-xs',
  },
  link: {
    primary: 'text-gray-50',
    secondary: 'text-gray-300 hover:text-gray-50',
  },
  placeholder: 'text-gray-400',
} as const

/**
 * Status Typography System
 * 
 * Typography patterns for status indicators and state messages.
 */
export const statusTypography = {
  success: 'text-green-400',
  error: 'text-red-500',
  warning: 'text-orange-400',
  info: 'text-blue-500',
  loading: 'text-blue-500',
  completed: 'text-green-400',
  failed: 'text-red-400',
  processing: 'text-blue-400',
} as const

/**
 * Badge Typography System
 * 
 * Typography patterns for badges and small indicators.
 */
export const badgeTypography = {
  primary: 'text-xs',
  secondary: 'text-xs',
  count: 'ml-1 text-xs',
  status: 'text-sm px-2 py-1 rounded-md',
  outline: 'text-xs font-mono',
} as const

/**
 * Type definitions for better TypeScript support
 */
export type HeadingLevel = keyof typeof headingTypography
export type HeadingVariant<T extends HeadingLevel> = keyof typeof headingTypography[T]
export type BodyVariant = keyof typeof bodyTypography
export type CodeVariant = keyof typeof codeTypography
export type InteractiveVariant = keyof typeof interactiveTypography
export type StatusVariant = keyof typeof statusTypography
export type BadgeVariant = keyof typeof badgeTypography

/**
 * Helper function to get heading typography classes
 */
export function getHeadingClasses<T extends HeadingLevel>(
  level: T,
  variant: keyof typeof headingTypography[T]
): string {
  return headingTypography[level][variant] as string
}

/**
 * Helper function to get body typography classes
 */
export function getBodyClasses(variant: BodyVariant): string {
  return bodyTypography[variant]
}

/**
 * Helper function to get code typography classes
 */
export function getCodeClasses(variant: CodeVariant): string {
  return codeTypography[variant]
}

/**
 * Helper function to get interactive typography classes
 */
export function getInteractiveClasses(element: keyof typeof interactiveTypography, variant?: string): string {
  const elementClasses = interactiveTypography[element]
  if (typeof elementClasses === 'string') {
    return elementClasses
  }
  if (variant && variant in elementClasses) {
    return elementClasses[variant as keyof typeof elementClasses]
  }
  return ''
}

/**
 * Helper function to get status typography classes
 */
export function getStatusClasses(variant: StatusVariant): string {
  return statusTypography[variant]
}

/**
 * Helper function to get badge typography classes
 */
export function getBadgeClasses(variant: BadgeVariant): string {
  return badgeTypography[variant]
}

/**
 * Common typography combinations used throughout the app
 */
export const commonTypographyCombinations = {
  pageTitle: 'text-4xl font-medium text-center',
  sectionHeader: 'text-lg font-semibold',
  cardTitle: 'text-sm font-medium',
  taskTitle: 'text-lg font-medium text-gray-50',
  brandTitle: 'text-xl font-semibold text-gray-50',
  bodyText: 'text-gray-300',
  mutedText: 'text-gray-400',
  detailText: 'text-gray-400 text-sm',
  codeInline: 'font-mono text-xs',
  codeBlock: 'font-mono text-sm whitespace-pre-wrap',
  timestamp: 'text-xs text-gray-500 font-mono',
  buttonPrimary: 'text-black',
  buttonSecondary: 'text-gray-300',
  statusSuccess: 'text-green-400',
  statusError: 'text-red-500',
  statusLoading: 'text-blue-500',
  badge: 'text-xs',
  badgeCount: 'ml-1 text-xs',
} as const

/**
 * Validation function to ensure typography tokens are properly defined
 */
export function validateTypographyTokens(): {
  valid: boolean
  issues: string[]
} {
  const issues: string[] = []
  
  // Check that required typography patterns exist
  const requiredPatterns = [
    'pageTitle',
    'sectionHeader',
    'cardTitle',
    'bodyText',
    'codeBlock',
    'timestamp',
  ]
  
  for (const pattern of requiredPatterns) {
    if (!commonTypographyCombinations[pattern as keyof typeof commonTypographyCombinations]) {
      issues.push(`Typography pattern missing: ${pattern}`)
    }
  }
  
  return {
    valid: issues.length === 0,
    issues
  }
}