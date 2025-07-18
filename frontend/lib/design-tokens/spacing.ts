/**
 * Spacing Design Tokens
 * 
 * This file contains spacing patterns extracted from existing components.
 * All spacing classes are designed to work with Tailwind CSS v3.4.17.
 * 
 * Phase 1: Extract existing spacing patterns to establish baseline
 * Phase 2: These tokens will be gradually adopted by components
 */

/**
 * Container Spacing System
 * 
 * Spacing patterns for containers, layouts, and main content areas.
 */
export const containerSpacing = {
  page: 'container mx-auto max-w-3xl py-16',
  header: 'container mx-auto px-4 py-4',
  content: 'flex-1 overflow-y-auto p-4',
  sidebar: 'w-80 p-4',
  main: 'flex-1 flex flex-col',
  card: 'p-4',
  cardHeader: 'pb-3',
  cardContent: 'p-0 pt-6',
} as const

/**
 * Gap Spacing System
 * 
 * Spacing patterns for gaps between elements in flex and grid layouts.
 */
export const gapSpacing = {
  xs: 'gap-1',
  sm: 'gap-2',
  md: 'gap-3',
  lg: 'gap-4',
  xl: 'gap-6',
  buttons: 'gap-2',
  form: 'gap-4',
  list: 'gap-2',
  tabs: 'gap-2',
  icons: 'gap-2',
  sections: 'gap-6',
} as const

/**
 * Margin Spacing System
 * 
 * Spacing patterns for margins around elements.
 */
export const marginSpacing = {
  xs: 'mb-2',
  sm: 'mb-4',
  md: 'mb-6',
  lg: 'mb-8',
  xl: 'mb-10',
  auto: 'mt-auto',
  section: 'mb-8',
  title: 'mb-4',
  element: 'mb-2',
  icon: 'mr-2',
  iconSmall: 'ml-1',
  buttonIcon: 'mr-2',
  badge: 'ml-2',
} as const

/**
 * Padding Spacing System
 * 
 * Spacing patterns for padding inside elements.
 */
export const paddingSpacing = {
  xs: 'p-2',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
  button: 'px-4 py-1',
  badge: 'px-1.5 py-0.5',
  badgeSecondary: 'px-2 py-1',
  input: 'px-3 py-2',
  card: 'p-4',
  cardSmall: 'p-2',
  code: 'p-3',
  tab: 'px-4',
  listItem: 'py-2 px-3',
  hover: 'p-3',
  section: 'space-y-6',
  list: 'space-y-1',
  form: 'space-y-4',
  logs: 'space-y-2',
  errors: 'space-y-4',
} as const

/**
 * Layout Spacing System
 * 
 * Spacing patterns for specific layout components and sections.
 */
export const layoutSpacing = {
  headerHeight: 'h-full',
  contentHeight: 'h-[500px]',
  sidebarWidth: 'w-80',
  fullWidth: 'w-full',
  autoWidth: 'w-auto',
  maxWidth: 'max-w-2xl',
  minWidth: 'min-w-0',
  flexShrink: 'flex-shrink-0',
  flex1: 'flex-1',
  grid: 'grid-cols-2 md:grid-cols-4',
  gridTabs: 'grid-cols-5',
  gridButtons: 'grid-cols-6',
} as const

/**
 * Component-Specific Spacing
 * 
 * Spacing patterns for specific UI components.
 */
export const componentSpacing = {
  agentOutput: {
    container: 'space-y-4',
    panel: 'h-full',
    content: 'space-y-0',
    line: 'py-2 px-3',
    summary: 'space-y-6 text-sm',
    sidebar: 'space-y-2',
  },
  task: {
    container: 'space-y-1',
    item: 'p-3 rounded-lg',
    content: 'flex flex-col',
    stats: 'grid grid-cols-2 md:grid-cols-4 gap-4 text-sm',
  },
  tabs: {
    list: 'border-b border-gray-800 rounded-none w-full justify-start bg-transparent p-0',
    trigger: 'rounded-none',
    content: 'mt-6 space-y-1',
  },
  form: {
    container: 'bg-gray-900/80 border border-gray-800 rounded-xl p-4 space-y-4',
    controls: 'flex items-center justify-between',
    inputs: 'flex items-center gap-2',
    buttons: 'flex items-center gap-2',
  },
  loading: {
    container: 'flex items-center justify-center',
    content: 'text-center',
    spinner: 'animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4',
  },
} as const

/**
 * Type definitions for better TypeScript support
 */
export type ContainerSpacingVariant = keyof typeof containerSpacing
export type GapSpacingVariant = keyof typeof gapSpacing
export type MarginSpacingVariant = keyof typeof marginSpacing
export type PaddingSpacingVariant = keyof typeof paddingSpacing
export type LayoutSpacingVariant = keyof typeof layoutSpacing

/**
 * Helper function to get container spacing classes
 */
export function getContainerSpacing(variant: ContainerSpacingVariant): string {
  return containerSpacing[variant]
}

/**
 * Helper function to get gap spacing classes
 */
export function getGapSpacing(variant: GapSpacingVariant): string {
  return gapSpacing[variant]
}

/**
 * Helper function to get margin spacing classes
 */
export function getMarginSpacing(variant: MarginSpacingVariant): string {
  return marginSpacing[variant]
}

/**
 * Helper function to get padding spacing classes
 */
export function getPaddingSpacing(variant: PaddingSpacingVariant): string {
  return paddingSpacing[variant]
}

/**
 * Helper function to get layout spacing classes
 */
export function getLayoutSpacing(variant: LayoutSpacingVariant): string {
  return layoutSpacing[variant]
}

/**
 * Helper function to get component-specific spacing
 */
export function getComponentSpacing(component: keyof typeof componentSpacing, variant: string): string {
  const componentSpacingObj = componentSpacing[component]
  if (typeof componentSpacingObj === 'object' && variant in componentSpacingObj) {
    return componentSpacingObj[variant as keyof typeof componentSpacingObj]
  }
  return ''
}

/**
 * Common spacing combinations used throughout the app
 */
export const commonSpacingCombinations = {
  pageLayout: 'container mx-auto max-w-3xl py-16',
  cardLayout: 'p-4 space-y-4',
  formLayout: 'space-y-4',
  listLayout: 'space-y-1',
  sectionLayout: 'space-y-6',
  buttonGroup: 'flex items-center gap-2',
  iconButton: 'flex items-center gap-2',
  tabsLayout: 'border-b border-gray-800 rounded-none w-full justify-start bg-transparent p-0',
  contentPadding: 'p-4',
  sidebarPadding: 'p-4',
  listItem: 'py-2 px-3',
  badgeSpacing: 'px-2 py-1',
  codeBlock: 'p-3',
  loadingContainer: 'flex items-center justify-center',
} as const

/**
 * Validation function to ensure spacing tokens are properly defined
 */
export function validateSpacingTokens(): {
  valid: boolean
  issues: string[]
} {
  const issues: string[] = []
  
  // Check that required spacing patterns exist
  const requiredPatterns = [
    'pageLayout',
    'cardLayout',
    'formLayout',
    'listLayout',
    'buttonGroup',
    'contentPadding',
    'listItem',
  ]
  
  for (const pattern of requiredPatterns) {
    if (!commonSpacingCombinations[pattern as keyof typeof commonSpacingCombinations]) {
      issues.push(`Spacing pattern missing: ${pattern}`)
    }
  }
  
  return {
    valid: issues.length === 0,
    issues
  }
}