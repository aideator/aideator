# Design Tokens System - Phase 1

This directory contains the foundational design token system for the AIdeator frontend. The system is designed to centralize and standardize visual design elements while maintaining compatibility with existing components.

## 🎯 Phase 1 Goals

- **Establish baseline**: Extract existing design patterns into reusable tokens
- **Maintain compatibility**: All functions return identical values to current hardcoded implementations  
- **Enable gradual adoption**: Components can adopt tokens incrementally without breaking changes
- **Provide validation**: Comprehensive testing ensures tokens work correctly

## 📁 File Structure

```
design-tokens/
├── README.md           # This file
├── index.ts           # Main entry point and exports
├── colors.ts          # Color system tokens
├── typography.ts      # Typography system tokens
├── spacing.ts         # Spacing system tokens
├── validation.ts      # Validation framework
├── test-tokens.ts     # Test suite
└── demo.ts           # Demo and examples
```

## 🎨 Color System

The color system provides tokens for:

- **Agent colors**: Visual differentiation between agent variations
- **Output type colors**: Color-coding for different types of output
- **Status colors**: Colors for task status indicators
- **UI element colors**: Common color patterns for UI components

### Usage Example

```typescript
import { getAgentColorClasses, getOutputTypeColorClasses } from '@/lib/design-tokens'

// Get agent color classes (returns exact same value as current hardcoded implementation)
const agentClasses = getAgentColorClasses(0)
// Returns: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20'

// Get output type color classes
const outputClasses = getOutputTypeColorClasses('stdout')
// Returns: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
```

## 📝 Typography System

The typography system provides tokens for:

- **Headings**: Different heading levels and variants
- **Body text**: Primary, secondary, and muted text styles
- **Code**: Monospace styles for code, logs, and technical content
- **Interactive elements**: Button and link typography
- **Status text**: Typography for status messages

### Usage Example

```typescript
import { getHeadingClasses, getBodyClasses, getCodeClasses } from '@/lib/design-tokens'

// Get heading classes
const titleClasses = getHeadingClasses('h1', 'primary')
// Returns: 'text-4xl font-medium text-center'

// Get body classes
const textClasses = getBodyClasses('primary')
// Returns: 'text-gray-300'

// Get code classes
const codeClasses = getCodeClasses('block')
// Returns: 'font-mono text-sm whitespace-pre-wrap'
```

## 📐 Spacing System

The spacing system provides tokens for:

- **Container spacing**: Layout containers and content areas
- **Gap spacing**: Gaps between elements in flex/grid layouts
- **Margin spacing**: Margins around elements
- **Padding spacing**: Padding inside elements
- **Component spacing**: Spacing patterns for specific components

### Usage Example

```typescript
import { getContainerSpacing, getGapSpacing, getPaddingSpacing } from '@/lib/design-tokens'

// Get container spacing
const pageLayout = getContainerSpacing('page')
// Returns: 'container mx-auto max-w-3xl py-16'

// Get gap spacing
const buttonGap = getGapSpacing('buttons')
// Returns: 'gap-2'

// Get padding spacing
const cardPadding = getPaddingSpacing('card')
// Returns: 'p-4'
```

## 🔧 Utility Functions

### Token Combination

```typescript
import { combineDesignTokens, componentTokens } from '@/lib/design-tokens'

// Combine multiple tokens
const cardClasses = combineDesignTokens(
  getAgentColorClasses(0),
  getContainerSpacing('card'),
  'rounded-lg border'
)

// Use pre-configured component tokens
const agentCard = componentTokens.agentOutput.getVariationCardClasses(0)
```

### Validation and Testing

```typescript
import { runAllTests, validateDesignTokens, quickTest } from '@/lib/design-tokens'

// Run all tests
const testsPassed = runAllTests()

// Run validation
const validation = validateDesignTokens()
if (!validation.valid) {
  console.error('Validation issues:', validation.issues)
}

// Quick smoke test
quickTest()
```

## 🧪 Testing and Validation

The design token system includes comprehensive testing:

### Test Suite (`test-tokens.ts`)

- **Compatibility tests**: Verify tokens return identical values to hardcoded implementations
- **Helper function tests**: Test all helper functions with various inputs
- **Edge case tests**: Test fallback behavior and error handling

### Validation Framework (`validation.ts`)

- **Token completeness**: Ensure all required tokens are defined
- **Value validation**: Check that tokens return expected values
- **Tailwind validation**: Verify classes follow Tailwind CSS patterns
- **Function validation**: Test all helper functions work correctly

### Running Tests

```bash
# In browser console or Node.js
import { runAllTests } from '@/lib/design-tokens'
runAllTests()

# Quick test
import { quickTest } from '@/lib/design-tokens'
quickTest()
```

## 🚀 Usage in Components

### Current (Hardcoded)

```typescript
const agentColors = {
  0: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
  1: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
  // ...
}

const agentColorClass = agentColors[variationId] || agentColors[0]
```

### Future (With Tokens)

```typescript
import { getAgentColorClasses } from '@/lib/design-tokens'

const agentColorClass = getAgentColorClasses(variationId)
```

**Note**: Both approaches return identical values during Phase 1.

## 🎨 Design Philosophy

### Tailwind CSS v3.4.17 Compliance

- All tokens use complete Tailwind class names
- No dynamic class interpolation (e.g., `text-${color}-500`)
- All classes are statically analyzable by Tailwind's purge process

### Backward Compatibility

- All helper functions return identical strings to current implementations
- No breaking changes to existing components
- Gradual adoption path

### Type Safety

- Full TypeScript support with proper type definitions
- Intellisense support for all token variants
- Compile-time validation of token usage

## 📈 Future Phases

### Phase 2: Component Adoption

- Gradually replace hardcoded values with design tokens
- Update components one at a time
- Maintain backward compatibility

### Phase 3: Advanced Features

- Theme switching capabilities
- Component variants system
- Design system documentation

## 💡 Development Tips

### Adding New Tokens

1. Add token to appropriate file (`colors.ts`, `typography.ts`, `spacing.ts`)
2. Update validation in `validation.ts`
3. Add tests in `test-tokens.ts`
4. Update this README

### Debugging

```typescript
import { devUtils } from '@/lib/design-tokens'

// Log all tokens
devUtils.logTokens()

// Check if token exists
devUtils.hasToken('agentColors.0')

// Get token value
devUtils.getToken('agentColors.0')
```

## 🔍 Common Patterns

### Agent Output Viewer

```typescript
// Get agent variation card classes
const cardClasses = componentTokens.agentOutput.getVariationCardClasses(variationId)

// Get output type badge classes  
const badgeClasses = componentTokens.agentOutput.getOutputLineClasses(outputType)
```

### Task Status

```typescript
// Get status indicator classes
const statusClasses = componentTokens.task.getStatusClasses(status)
```

### Layout

```typescript
// Get page layout classes
const pageClasses = componentTokens.ui.layout.page
const containerClasses = componentTokens.ui.layout.container
```

## 🏗️ Implementation Status

- ✅ **Colors**: Complete with all agent and output type colors
- ✅ **Typography**: Complete with headings, body, and code styles
- ✅ **Spacing**: Complete with container, gap, margin, and padding tokens
- ✅ **Validation**: Complete with comprehensive test suite
- ✅ **Testing**: Complete with compatibility and edge case tests
- ✅ **Documentation**: Complete with usage examples and API reference

## 📚 Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Design System Best Practices](https://designsystemchecklist.com/)
- [Component-driven Development](https://www.componentdriven.org/)

---

*Simple and powerful, the design token system is. Consistent visual language, it provides.*