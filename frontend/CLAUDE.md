# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AIdeator Frontend - Instructions for Claude

This is the **Next.js 15 frontend** for AIdeator, a Kubernetes-native LLM orchestration platform that runs multiple AI agents in isolated containers and streams their output in real-time.

## 🏗️ Architecture

### Tech Stack
- **Framework**: Next.js 15.2.4 with App Router and Turbopack
- **React**: Version 19.0.0 (latest)
- **TypeScript**: Version 5 with strict mode
- **Styling**: Tailwind CSS v4.1.11 with PostCSS v4
- **UI Components**: shadcn/ui with Radix UI primitives
- **Real-time**: Server-Sent Events (SSE) for agent streaming

### Project Structure
```
app/                     # Next.js 15 App Router
├── page.tsx            # Homepage (redirects to /stream)
├── stream/page.tsx     # Multi-agent streaming interface
├── runs/[runId]/       # Run details page
├── layout.tsx          # Root layout with Geist fonts
└── globals.css         # Tailwind v4 imports and theme

components/
├── agents/             # Agent-specific components
│   ├── StreamCard.tsx  # Individual agent stream display
│   └── StreamGrid.tsx  # Multi-agent grid layout
├── ui/                 # shadcn/ui components
└── Various page components

hooks/
├── useAgentStream.ts   # SSE streaming hook
└── useAPI.ts          # API client hook

lib/
├── api.ts             # Backend API client
├── utils.ts           # clsx + tailwind-merge utility
└── types.ts           # TypeScript interfaces
```

## 🚀 Development Commands

```bash
# Development with Turbopack (fast refresh)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Linting
npm run lint

# Type checking
npm run type-check

# Unit tests (Jest)
npm test
npm run test:watch

# E2E tests (Playwright)
npm run test:e2e          # Run all tests
npm run test:e2e:ui       # Interactive UI mode
npm run test:e2e:debug    # Debug mode
```

## 🎨 Design System

### Tailwind CSS v4 Configuration

The frontend uses Tailwind CSS v4 with custom CSS properties for theming:

```css
/* Primary Colors */
--ai-primary: 239 79% 59%;      /* Deep indigo */
--ai-secondary: 258 90% 67%;    /* Purple */
--ai-accent: 188 100% 50%;      /* Cyan */

/* Agent Colors (1-5) */
--agent-1: 0 84% 60%;           /* Red */
--agent-2: 39 96% 51%;          /* Amber */
--agent-3: 160 84% 39%;         /* Emerald */
--agent-4: 221 83% 53%;         /* Blue */
--agent-5: 258 90% 67%;         /* Purple */
```

### Tailwind v4 Critical Differences

1. **CSS Import Syntax** (globals.css):
   ```css
   /* ✅ CORRECT v4 syntax */
   @import "tailwindcss";
   
   /* ❌ WRONG - Old v3 syntax */
   @tailwind base;
   ```

2. **PostCSS Configuration**:
   ```js
   // ✅ CORRECT v4 plugin
   "@tailwindcss/postcss": {}
   
   // ❌ WRONG - Old v3 plugin
   // tailwindcss: {}
   ```

3. **Avoid Dynamic Classes**:
   ```tsx
   // ❌ BAD - May be purged
   className={`bg-agent-${index}`}
   
   // ✅ GOOD - Complete class names
   className={index === 1 ? 'bg-agent-1' : 'bg-agent-2'}
   ```

## 🔌 API Integration

The frontend expects the FastAPI backend at `http://localhost:8000`:

### Key Endpoints
- `POST /api/v1/runs` - Create new agent run
- `GET /api/v1/runs/{runId}` - Get run details
- `GET /api/v1/runs/{runId}/stream` - SSE stream of agent output
- `POST /api/v1/runs/{runId}/select` - Select winning variation

### SSE Streaming Hook

The `useAgentStream` hook manages real-time streaming:
```typescript
const { streams, isStreaming, error, startStream, stopStream } = useAgentStream();

// streams: Map<variation_id, string[]> - Output per agent
// startStream(runId) - Begin streaming
// stopStream() - Clean up connection
```

## 🧪 Testing

### E2E Tests with Playwright

Tests run on port 3001 and expect backend on port 8000:

```bash
# Run all tests
npm run test:e2e

# Debug specific test
npm run test:e2e:debug tests/e2e/streaming.spec.ts

# View test report
npx playwright show-report
```

Test files:
- `homepage.spec.ts` - Landing page tests
- `streaming.spec.ts` - Agent streaming interface
- `smoke-test.spec.ts` - Basic functionality

### Environment Setup

For E2E tests to work:
1. Frontend runs on port 3001
2. Backend API expected at port 8000
3. Tests use mocked API responses by default

## 📋 Key Features

1. **Multi-Agent Streaming**: Real-time display of up to 5 agent outputs
2. **Responsive Grid**: Adapts from 1 to 5 columns based on viewport
3. **Connection Status**: Visual indicators for streaming state
4. **Agent Selection**: Choose winning variation with visual feedback
5. **Error Handling**: Comprehensive error states and recovery

## 🚨 Common Pitfalls

### What NOT to do
- ❌ Use Tailwind v3 syntax (`@tailwind base`)
- ❌ Create dynamic Tailwind classes with string interpolation
- ❌ Hardcode API URLs or ports
- ❌ Skip TypeScript types
- ❌ Ignore mobile responsiveness
- ❌ Mix shadcn/ui v0 patterns with current setup

### What TO do
- ✅ Use Tailwind v4 syntax (`@import "tailwindcss"`)
- ✅ Use complete Tailwind class names
- ✅ Configure API endpoints via environment variables
- ✅ Maintain full TypeScript coverage
- ✅ Test on mobile viewports
- ✅ Follow existing component patterns

## 🔧 Implementation Patterns

### Component Pattern
```tsx
// Use shadcn/ui components with CVA
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// Consistent prop interfaces
interface ComponentProps {
  className?: string
  children: React.ReactNode
}

// Tailwind v4 classes with theme variables
<div className={cn(
  "bg-neutral-paper rounded-lg p-lg",
  "border-l-4 border-agent-1",
  className
)}>
```

### API Error Handling
```typescript
try {
  const response = await createRun(data);
  // Handle success
} catch (error) {
  if (error instanceof APIError) {
    setError(error.message);
  } else {
    setError('An unexpected error occurred');
  }
}
```

### SSE Streaming Pattern
```typescript
// Clean up on unmount
useEffect(() => {
  return () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };
}, []);
```

## 🎯 Development Workflow

1. **Start Backend First**: Ensure API is running on port 8000
2. **Run Frontend Dev**: `npm run dev` (uses Turbopack)
3. **Make Changes**: Hot reload handles most updates
4. **Test Changes**: Run relevant E2E tests
5. **Type Check**: `npm run type-check` before committing
6. **Lint**: `npm run lint` to catch issues

## 📚 Key Dependencies

### Core
- `next`: 15.2.4 - React framework
- `react`: 19.0.0 - UI library
- `typescript`: ^5 - Type safety

### UI/Styling
- `tailwindcss`: 4.1.11 - Utility CSS
- `@tailwindcss/postcss`: 4.1.11 - PostCSS plugin
- `@radix-ui/*`: UI primitives
- `class-variance-authority`: Component variants
- `tailwind-merge`: Class merging
- `lucide-react`: Icons

### Testing
- `@playwright/test`: E2E testing
- `jest`: Unit testing (configured but no tests yet)

### Utilities
- `clsx`: Class name construction
- `date-fns`: Date formatting