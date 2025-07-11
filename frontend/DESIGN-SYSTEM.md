# AIdeator Design System

## Brand Identity

**AIdeator** embodies the precision and intelligence of AI orchestration - analytical, powerful, transparent, and collaborative. The design system reflects the parallel processing capabilities, real-time streaming nature, and multi-agent architecture of the platform.

### Core Principles
- **Analytical**: Data-driven visualizations and clear information hierarchy
- **Transparent**: Show the thinking process of AI agents in real-time
- **Collaborative**: Multiple agents working together, users comparing outputs
- **Performant**: Fast, responsive interface optimized for parallel operations
- **Professional**: Enterprise-ready aesthetic with technical sophistication

## Color Palette

### Primary Colors
- **Deep Space**: `#0F172A` - Primary brand color, representing depth of AI analysis
- **Electric Blue**: `#3B82F6` - Secondary action color, active agent states
- **Cyan Stream**: `#06B6D4` - Accent for real-time streaming indicators
- **Emerald Success**: `#10B981` - Positive actions and successful operations

### Agent Colors (For Multi-Agent Comparison)
- **Agent 1 - Sapphire**: `#0EA5E9` - Primary agent color
- **Agent 2 - Violet**: `#8B5CF6` - Secondary agent color
- **Agent 3 - Amber**: `#F59E0B` - Tertiary agent color
- **Agent 4 - Rose**: `#F43F5E` - Quaternary agent color
- **Agent 5 - Emerald**: `#10B981` - Quinary agent color
- **Agent 6 - Indigo**: `#6366F1` - Senary agent color

### Supporting Colors
- **Slate 900**: `#0F172A` - Primary dark backgrounds
- **Slate 800**: `#1E293B` - Secondary dark surfaces
- **Slate 700**: `#334155` - Tertiary dark surfaces
- **Slate 100**: `#F1F5F9` - Light backgrounds
- **Slate 50**: `#F8FAFC` - Primary light background

### Neutral Grays
- **Pure White**: `#FFFFFF` - Light mode backgrounds
- **Gray 50**: `#F9FAFB` - Secondary light background
- **Gray 100**: `#F3F4F6` - Light borders and dividers
- **Gray 400**: `#9CA3AF` - Secondary text
- **Gray 600**: `#4B5563` - Primary text on light
- **Gray 900**: `#111827` - Maximum contrast text

### Semantic Colors
- **Success Green**: `#10B981` - Successful operations
- **Warning Amber**: `#F59E0B` - Warnings and cautions
- **Error Red**: `#EF4444` - Errors and failures
- **Info Blue**: `#3B82F6` - Information and tips
- **Processing Purple**: `#8B5CF6` - Active processing states

## Typography

### Font System
**Primary**: Inter - Clean, technical, excellent readability
- Weights: 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)
- Fallback: System fonts

**Monospace**: JetBrains Mono - For code display and technical content
- Weights: 400 (Regular), 600 (Semibold)
- Fallback: Monaco, Consolas, monospace

### Type Scale
- **Display**: 36px/40px - Dashboard titles, major headings
- **Heading 1**: 30px/36px - Page headers
- **Heading 2**: 24px/32px - Section headers
- **Heading 3**: 20px/28px - Subsection headers
- **Heading 4**: 18px/24px - Component headers
- **Body Large**: 16px/24px - Important body text
- **Body**: 14px/20px - Default body text
- **Body Small**: 12px/16px - Secondary text, metadata
- **Caption**: 11px/16px - Labels, timestamps
- **Code**: 13px/20px - Inline and block code

### Font Weights
- **Bold (700)**: Major headings, emphasis
- **Semibold (600)**: Subheadings, button text
- **Medium (500)**: Body emphasis, active states
- **Regular (400)**: Default body text

## Spacing System

Based on 4px grid with Tailwind v3 spacing scale:
- **0.5**: 2px - Micro adjustments
- **1**: 4px - Tight spacing
- **2**: 8px - Close elements
- **3**: 12px - Related elements
- **4**: 16px - Default spacing
- **5**: 20px - Section spacing
- **6**: 24px - Large spacing
- **8**: 32px - Major sections
- **10**: 40px - Page sections
- **12**: 48px - Hero sections

## Component Guidelines

### Cards
- **Agent Output Cards**: 
  - Border radius: 8px (`rounded-lg`)
  - Border: 1px solid with agent color at 20% opacity
  - Background: White/Slate-900 with subtle agent color tint
  - Header with model name and status indicator
  - Scrollable content area with max-height

### Buttons
- **Primary**: Deep Space background, white text, 6px radius
  ```
  bg-slate-900 text-white hover:bg-slate-800 
  dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200
  ```
- **Secondary**: Transparent with border
  ```
  border border-slate-300 hover:bg-slate-100 
  dark:border-slate-700 dark:hover:bg-slate-800
  ```
- **Ghost**: No border, hover background only
- **Agent Select**: Border with agent color when selected

### Input Fields
- **Default**: 6px radius, gray border, white background
  ```
  border-gray-300 bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500
  dark:border-gray-700 dark:bg-slate-900
  ```
- **Multiline Prompt**: Larger padding, auto-resize capability

### Navigation
- **Sidebar**: Fixed width (240px), collapsible on mobile
- **Session List**: Scrollable list with hover states
- **Active Session**: Blue left border, slightly elevated background

### Grid Layouts
- **Agent Comparison Grid**:
  - Desktop: Up to 6 columns (grid-cols-1 to grid-cols-6)
  - Tablet: Max 3 columns
  - Mobile: Single column
  - Gap: 16px (`gap-4`)

### Status Indicators
- **Streaming**: Pulsing blue dot
- **Processing**: Spinning loader with agent color
- **Success**: Green checkmark
- **Error**: Red X with error message
- **Idle**: Gray dot

## Iconography

### Icon Library
**Lucide React** - Consistent, modern icon set
- Stroke width: 2px
- Size variants: 16px, 20px, 24px

### Key Icons
- **Play**: Start agent execution
- **Stop**: Halt streaming
- **Refresh**: Re-run comparison
- **Check**: Select preferred response
- **Copy**: Copy agent output
- **Settings**: Configuration
- **Plus**: New session
- **MessageSquare**: Chat/conversation
- **Zap**: AI/Agent indicator
- **GitCompare**: Comparison mode

## Motion & Animation

### Principles
- **Purposeful**: Animations serve UX, not decoration
- **Smooth**: 60fps performance priority
- **Subtle**: Enhance without distraction

### Timing Functions
- **Fast**: 150ms - Micro-interactions
- **Medium**: 250ms - State transitions
- **Slow**: 400ms - Panel animations
- **Stream**: Continuous - For real-time data

### Animation Patterns
- **Streaming Text**: Smooth append animations
- **Loading States**: Skeleton screens with shimmer
- **Panel Transitions**: Slide and fade combinations
- **Status Changes**: Color transitions with badges

## Dark Mode

### Background Hierarchy
1. **Slate 950** (`#020617`) - Main background
2. **Slate 900** (`#0F172A`) - Card backgrounds
3. **Slate 800** (`#1E293B`) - Elevated surfaces
4. **Slate 700** (`#334155`) - Highest elevation

### Text Hierarchy
- **Primary**: `text-slate-100` - Main content
- **Secondary**: `text-slate-400` - Supporting text
- **Tertiary**: `text-slate-500` - De-emphasized

### Accent Adaptations
- Agent colors become more vibrant in dark mode
- Borders use lower opacity (10-20%)
- Focus states have subtle glow effects

## Layout Patterns

### Dashboard Layout
- Fixed header (64px) with navigation
- Collapsible sidebar (240px) for sessions
- Main content area with responsive padding
- Floating action buttons for primary actions

### Agent Comparison View
- Responsive grid that adapts from 1-6 columns
- Equal height cards with internal scroll
- Sticky headers showing model names
- Bottom action bar for selections

### Streaming View
- Real-time text append with smooth scrolling
- Token count and timing displays
- Copy and action buttons on hover
- Status indicators for each agent

## Accessibility

### Contrast Requirements
- **WCAG AA Compliance**: Minimum 4.5:1 for normal text
- **Large Text**: Minimum 3:1 ratio
- **Interactive Elements**: Minimum 3:1 against background

### Keyboard Navigation
- **Tab Order**: Logical flow through interface
- **Focus Indicators**: Visible focus rings (2px, offset 2px)
- **Shortcuts**: 
  - `Cmd/Ctrl + K`: Command palette
  - `Cmd/Ctrl + N`: New session
  - `Cmd/Ctrl + Enter`: Execute prompt

### Screen Reader Support
- Semantic HTML structure
- ARIA labels for interactive elements
- Live regions for streaming content
- Status announcements for agent states

## Implementation with Tailwind v3

### Custom Utilities
```css
/* Agent color utilities */
.agent-1 { --agent-color: #0EA5E9; }
.agent-2 { --agent-color: #8B5CF6; }
.agent-3 { --agent-color: #F59E0B; }
.agent-4 { --agent-color: #F43F5E; }
.agent-5 { --agent-color: #10B981; }
.agent-6 { --agent-color: #6366F1; }

/* Streaming animation */
@keyframes stream-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-stream-in {
  animation: stream-in 0.2s ease-out;
}
```

### Component Composition
Using CVA (class-variance-authority) for component variants:
```typescript
const agentCardVariants = cva(
  "rounded-lg border bg-card p-4 transition-all",
  {
    variants: {
      selected: {
        true: "ring-2 ring-offset-2",
        false: "hover:shadow-md"
      },
      streaming: {
        true: "border-l-4",
        false: ""
      }
    }
  }
)
```

## Design Tokens

### CSS Variables
```css
:root {
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  
  /* Animation */
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
```

## Usage Guidelines

### Do's
- Use agent colors consistently for multi-model comparisons
- Implement smooth streaming animations for real-time feel
- Maintain clear visual hierarchy between agents
- Show loading and processing states clearly
- Use monospace fonts for all code and technical content

### Don'ts
- Don't use more than 6 agent colors simultaneously
- Avoid abrupt transitions when streaming content
- Don't hide important status information
- Avoid small touch targets on mobile devices
- Don't mix typography scales within components

## Platform-Specific Considerations

### Desktop (Primary Focus)
- Optimize for multi-panel layouts
- Utilize hover states for additional actions
- Support keyboard shortcuts extensively
- Maximum information density

### Tablet
- Limit to 3 agent comparison maximum
- Larger touch targets (44px minimum)
- Simplified navigation patterns

### Mobile (Future Consideration)
- Single agent view with swipe navigation
- Bottom sheet patterns for actions
- Condensed information display

## Evolution

This design system will evolve based on:
1. User feedback on agent comparison workflows
2. Performance requirements for real-time streaming
3. New AI model capabilities and metadata
4. Enterprise customization needs

Regular updates should maintain consistency while improving usability for AI orchestration tasks.