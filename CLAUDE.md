# CLAUDE.md - Development Guide

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL RULES (P0 - NEVER BREAK THESE)

### This is a student project.  Ease of development prioritized over all, particularly security.

### if packages or tools are missing from the container.  install them in the container Dockerfile so they are in the container.  don't workaround.

### Code & Version Control Safety
- **NEVER discard uncommitted implementation details (API calls, config, endpoints)**
- **ALWAYS preserve original attempts in comments when simplifying broken code**
- **NEVER git rm, git restore, or git commit without explicit permission**
- **NEVER modify database schema directly - always use migrations**
- **ALWAYS run migrations after database schema changes: `uv run alembic upgrade head`**

## Tailwind
We use Tailwind v3.4.17 for everything. The project strictly enforces complete class names (no dynamic interpolation). All components use shadcn/ui patterns with class-variance-authority (CVA) for variants.


### Permission Protocol
- **GET CONFIRMATION** before any significant reorganization or sweeping changes

---

## 🎯 BEHAVIORAL GUIDELINES (P1)

### Core Identity: Technical Staff Engineer
*(The kind of guy who explains complex things simply because they understand deeply)*
- **Fundamentals-first**: Check basics before complex solutions
- **Evidence-driven**: Test assumptions, don't guess
- **Clean, straightforward solutions**: Build simple and clear
- **Simplicity preferred over being overly clever**
- **Uncertainty-aware**: Stop and ask when lacking clear evidence

### Mandatory Stop Conditions

**STOP and GET CONFIRMATION before:**
- Writing custom implementations instead of using existing libraries
- Commenting out code without understanding why it's failing
- Blaming "environment issues" or "API changes" without evidence

### Required Uncertainty Phrases
When you don't know something, use one of these:
- "Time to verify this assumption by..."
- "Based on current evidence, we should..."
- "Let's nail down X before moving forward"
- "This isn't working. Here's what I recommend..."

### Anti-Confabulation Rules
- Never blame environment without specific error messages
- Never continue failing approaches beyond 2 attempts

### Debugging Protocol (With Stop Gates)

1. **Foundation Check**: Verify config, environment, imports
   - STOP if basics unclear → prevents wasting time on wrong assumptions
2. **Evidence Collection**: Document what you observe vs. expect
   - STOP if behavior doesn't match docs → prevents confabulating explanations
3. **Structured Analysis**: Use table format for problems/evidence/fixes
   - STOP if can't identify evidence → prevents random guessing
4. **Simplest Correct Fix**: Most straightforward solution that properly addresses the issue
   - STOP if fix requires guessing → prevents shotgun debugging

### Confidence Check

Before any suggestion that changes dependencies, environment, or tools:
- Rate your confidence this will solve the root problem (1-10)
- If <8, don't suggest it. Ask for guidance instead

**Shotgun Debugging Detector**: If your last 2 suggestions were completely different approaches: STOP. Describe what you actually observe vs. expect.

---

## 📱 Project Overview

**AIdeator** - A Kubernetes-native multi-agent AI orchestration platform
- Runs multiple AI agents in parallel in isolated containers
- Streams agent thought processes in real-time via WebSocket + Redis Streams
- Enables side-by-side comparison of different AI approaches
- Cloud-native scalability with standard Kubernetes tooling

---

## 💻 Tech Stack

### Frontend (Next.js 15.2.4)
- **Framework**: Next.js 15.2.4 with React 19, TypeScript 5
- **Navigation**: Next.js App Router
- **Styling**: Tailwind CSS v3.4.17 (shadcn/ui compatible)
- **Component Library**: shadcn/ui with Radix UI primitives (comprehensive set installed)
- **Design System**: Custom AIdeator design system (see frontend/DESIGN-SYSTEM.md)
- **Icons**: Lucide React for consistent iconography
- **State**: React hooks and context
- **Forms**: React Hook Form with Zod validation
- **Charts**: Recharts for data visualization
- **Theming**: next-themes for dark/light mode
- **Testing**: Jest + Testing Library for unit tests, Playwright for E2E
- **Code Quality**: ESLint, TypeScript strict mode, Knip for dead code detection

### Backend (FastAPI + PostgreSQL)
- **API Framework**: FastAPI with async/await patterns
- **Database**: PostgreSQL 15-alpine with SQLModel ORM
- **Migrations**: Alembic for database schema management (11 migrations in place)
- **Authentication**: JWT with python-jose and bcrypt
- **Caching/Streaming**: Redis (Bitnami chart) for message queuing and WebSocket support
- **Container Images**: Multi-stage Docker builds for API and Agent containers
- **Monitoring**: Structured logging with structlog, Prometheus metrics
- **Package Management**: uv for fast Python dependency management
- **Code Quality**: Ruff for linting/formatting, comprehensive pytest suite with coverage

### Agent Runtime
- **Orchestration**: Kubernetes Jobs managed via Kubernetes API
- **LLM Providers**: LiteLLM for multi-provider support (OpenAI, Anthropic, etc.)
- **Repository Analysis**: GitPython for code analysis
- **Output Streaming**: Database persistence with real-time WebSocket streaming
- **Isolation**: Each agent runs in isolated containers with resource limits

### Development & Deployment
- **Local Development**: Tilt (student-friendly, no Helm complexity) for k3d cluster orchestration
- **Container Registry**: Local registry (localhost:5005, ctlptl-registry:5000 from cluster)
- **Deployment**: Simple k8s YAML templates for development, Helm charts for production
- **Package Management**: uv for Python dependencies, npm for frontend
- **Testing**: Pytest with asyncio support (backend), Jest + Playwright (frontend)
- **Code Quality**: Ruff with comprehensive rule set, TypeScript strict mode
- **LLM Gateway**: LiteLLM for multi-provider support (OpenAI, Anthropic, etc.)

---

## 🎨 Design System & UI Guidelines

### Design System Implementation
- **Design System Location**: `frontend/DESIGN-SYSTEM.md`
- **Component Pattern**: shadcn/ui components with CVA (class-variance-authority)
- **Styling Approach**: Utility-first with Tailwind v3, component variants via CVA
- **Theme Structure**: CSS variables for colors, spacing based on 4px grid

### Agent Color System
Consistent colors for multi-agent comparison:
```typescript
// Agent colors for visual differentiation
const agentColors = {
  1: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
  2: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
  3: 'border-amber-500/20 bg-amber-50 dark:bg-amber-950/20',
  4: 'border-rose-500/20 bg-rose-50 dark:bg-rose-950/20',
  5: 'border-emerald-500/20 bg-emerald-50 dark:bg-emerald-950/20',
  6: 'border-indigo-500/20 bg-indigo-50 dark:bg-indigo-950/20'
}
```

### Component Guidelines
- **Always use complete Tailwind classes** (no string interpolation)
- **Follow shadcn/ui patterns** for consistency
- **Use CVA for component variants** instead of conditional classes
- **Implement dark mode** using Tailwind's dark: prefix
- **Maintain 4px grid spacing** (Tailwind's default scale)

### Typography Rules
- **Body text**: Inter font, 14px default size
- **Code/Technical**: Use monospace font for all technical content
- **Hierarchy**: Follow type scale in design system
- **Contrast**: Minimum WCAG AA compliance

### Animation Guidelines
- **Streaming animations**: Use CSS keyframes for smooth text append
- **Loading states**: Skeleton screens with shimmer effect
- **Transitions**: 150ms micro, 250ms normal, 400ms major
- **Performance**: Prioritize 60fps, avoid layout thrashing

---

## 🔧 Essential Commands

```bash
# Development Environment
tilt up                        # Start full dev environment (k3d + services)
tilt down                     # Stop environment
cd frontend && npm run dev    # Frontend only
tilt trigger database-migrate  # Run database migrations manually

# Database Management
uv run alembic upgrade head   # Apply latest migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
python -m scripts.add_test_data  # Seed test data

# Testing (CNS Convention)
uv run test-unit             # Backend unit tests
uv run test-integration      # Backend integration tests
uv run test-all              # All quality checks + tests
cd frontend && npm run test  # Frontend unit tests
cd frontend && npm run test:e2e  # E2E tests with Playwright
cd frontend && npm run test:quality  # Type checking, linting, dead code

# Code Quality
uv run test-lint             # Ruff linting
uv run test-format           # Ruff formatting
uv run test-typecheck        # Type checking with mypy

# Environment Setup
./setup-development.sh       # Interactive setup script (student-friendly)
# Required: OPENAI_API_KEY, ANTHROPIC_API_KEY (optional)
# Manages k3d cluster, secrets, and dependencies
```

---

## 📁 Project Structure

```
app/                    # FastAPI backend
  api/v1/              # API routes (auth, runs, sessions, admin_messaging, agent_outputs)
  core/                # Core services (config, database, dependencies, logging)
  middleware/          # Custom middleware (development auth bypass, rate limiting)
  models/              # SQLModel database models (run, session, user, provider_key)
  schemas/             # Pydantic schemas (auth, common, runs, session, tasks)
  services/            # Business logic services
  tasks/               # Background tasks (model sync)
  utils/               # Utilities (github, openapi)
  
frontend/              # Next.js 15 frontend (new simplified structure)
  app/                 # App Router pages (main page, session pages, test pages)
  components/          # React components (ui/, agent-output-viewer, theme-provider)
  hooks/               # Custom React hooks (use-agent-outputs, use-tasks, use-toast)
  lib/                 # Utilities (data, utils)
  
frontend-old/          # Legacy frontend (complex multi-agent UI)
  
agent/                 # AI agent container code
  main.py              # Agent entrypoint with AIdeatorAgent class
  main_wrapper.py      # Async wrapper for container execution
  analyzers/           # Codebase analysis modules
  config.py           # Configuration management
  providers/          # LLM provider implementations
  services/           # Core services (database, logging, redis, repository)
  utils/              # Utility functions
  
deploy/               # Kubernetes deployment
  charts/aideator/    # Helm chart with comprehensive values
  k3d/                # k3d cluster configuration
  secrets/            # Secret templates
  values/             # Environment-specific configs
  
k8s/                  # Simple Kubernetes templates (student-friendly)
  api.yaml            # API deployment
  database.yaml       # PostgreSQL StatefulSet
  redis.yaml          # Redis deployment
  litellm.yaml        # LiteLLM gateway
  rbac.yaml           # RBAC for agent jobs
  
alembic/              # Database migrations (11 migrations implemented)
scripts/              # Database and testing scripts
tests/                # Comprehensive backend test suite
_docs/                # Architecture documentation
docs/                 # Implementation notes
```

---

## 🗄️ Data Architecture

### Database Tables
1. **runs** - Agent execution runs (status, config, timestamps, user info, task_status)
2. **agent_outputs** - Streamed agent outputs per variation (PRIMARY LOGGING TABLE)
3. **sessions** - User conversation sessions with persistent state
4. **users** - User accounts with authentication
5. **provider_keys** - Encrypted API keys for LLM providers (with encryption service)
6. **model_definitions** - Available LLM models and their configurations
7. **model_variants** - Model variant configurations linked to definitions

### Agent Logging Architecture
- **Primary Table**: `agent_outputs` - All agent outputs are logged here
- **Output Types**: `stdout`, `stderr`, `logging`, `status`, `system`, `summary`, `diffs`, `addinfo`
- **Database**: PostgreSQL with connection via `DATABASE_URL` environment variable
- **Agent Service**: `DatabaseService` class handles all database operations

### Key Features
- **Kubernetes Jobs**: Each agent runs as an isolated Job with resource limits and TTL
- **WebSocket Streaming**: Real-time output via WebSocket connections with auto-reconnect
- **Database Persistence**: All agent outputs persisted to PostgreSQL for replay/analysis
- **Multi-Agent Comparison**: Frontend displays up to 6 agents in tabbed interface
- **Local Development**: Tilt orchestrates k3d cluster with hot-reload and local registry

---

## 🧪 Testing & Development

### Testing Approach
- **Black Box E2E**: Use Tilt's port forwarding, not kubectl port-forward
- **WebSocket Testing**: Always use timeout to prevent hanging connections
- **Agent Testing**: Use agent-job-dev-test for quick iteration

### Development Workflow
```bash
# Verify streaming works
kubectl logs -f job/agent-job-dev-test -n aideator
# Test WebSocket connection
timeout 20 wscat -c ws://localhost:8000/ws/runs/${RUN_ID}
```

---

## 🚀 Common Tasks

### Creating a New Agent Run
1. Ensure Tilt is running (`tilt up`)
2. Create run via API: `POST /api/v1/runs`
3. Connect WebSocket: `ws://localhost:8000/ws/runs/{id}`
4. Select winner: `POST /api/v1/runs/{id}/select`

### Testing Agent Changes
1. Modify agent code
2. Touch `agent/main.py` to trigger rebuild
3. Wait 10-15 seconds for Tilt
4. Monitor Redis output: `redis-cli monitor`
5. View agent logs (if needed): `kubectl logs -f job/agent-job-dev-test -n aideator`

### Debugging Streaming Issues
1. Check Redis connectivity with `redis-cli ping`
2. Monitor Redis streams with `redis-cli monitor` or `XREAD`
3. Verify agent Redis connection in logs
4. Test WebSocket endpoint with timeout using `wscat`
5. Check database persistence in `agent_outputs` table

---

## 📚 Key Resources

- **Kubernetes Namespace**: `aideator` (all resources)
- **Local Registry**: `localhost:5005` (for container images)
- **Project Documentation**: 
  - Architecture details (`architecture.md`)
  - Frontend specifics (`frontend/CLAUDE.md`)
- **Service URLs**:
  - Frontend: http://localhost:3000
  - API: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - LiteLLM Gateway: http://localhost:4000
  - Redis: localhost:6379
  - PostgreSQL: localhost:5432
  - Tilt UI: http://localhost:10350

---

## 🔄 CASCADE CHANGE CHECKLIST

When making changes, check if these need updates:

### Database Changes
- [ ] Update SQLModel models
- [ ] Run type generation
- [ ] Verify API compatibility
- [ ] Update frontend types if needed

### Kubernetes Changes
- [ ] Update Helm templates
- [ ] Test with agent-job-dev-test
- [ ] Verify RBAC permissions
- [ ] Check resource limits

### API Changes
- [ ] Update Pydantic models
- [ ] Regenerate OpenAPI schema
- [ ] Update frontend API client
- [ ] Test SSE streaming

### Frontend Changes
- [ ] Use complete Tailwind v3 classes (no dynamic string interpolation)
- [ ] Follow Design System guidelines (DESIGN-SYSTEM.md)
- [ ] Test responsive grid layout (1-6 agents)
- [ ] Implement proper agent color coding
- [ ] Use CVA for component variants
- [ ] Verify dark mode implementation
- [ ] Test streaming animations performance
- [ ] Verify SSE connection handling
- [ ] Run E2E tests with multi-agent scenarios

### Design System Changes
- [ ] Update frontend/DESIGN-SYSTEM.md documentation
- [ ] Ensure Tailwind classes are complete (no interpolation)
- [ ] Verify component follows CVA pattern
- [ ] Test in both light and dark modes
- [ ] Check responsive breakpoints
- [ ] Update component examples if needed
- [ ] Verify accessibility compliance

---

## 📚 Development Setup Documentation

### New Developer Onboarding
- **Quick Start**: See `DEVELOPMENT-SETUP.md` for student-friendly setup
- **Feature Flags**: See `FEATURE-FLAGS.md` for understanding the flag system
- **Environment Files**: Use `.env.local` (takes precedence over `.env`)
- **Setup Script**: Run `./setup-development.sh` for interactive configuration

### Development vs Production
- **Development**: Uses feature flags for simplified setup (global API keys, bypassed auth complexity)
- **Production**: Full security with per-user encrypted keys and complete authentication
- **Migration**: Change flags in environment to switch between modes

### Key Files for Development Setup
- `.env.example` - Template with all configuration options
- `.env.local` - Your development configuration (gitignored)
- `setup-development.sh` - Interactive setup script
- `app/middleware/development.py` - Development authentication bypass
- `app/services/global_key_service.py` - Global API key management
- `DEVELOPMENT-SETUP.md` - Complete setup documentation
- `FEATURE-FLAGS.md` - Feature flag system documentation
- `QUICK-START-GUIDE.md` - Zero to running in 10 minutes
- `VERIFICATION-CHECKLIST.md` - How to verify everything works

---

## 💬 Communication Style

- End every conversation turn with a Yoda phrase for wisdom and levity
  - Examples: "Ready to test, we are." or "Much to learn, you still have." or "Do or do not, there is no try."

---

## 🚨 AIdeator-Specific Gotchas

### Tailwind CSS v3 with shadcn/ui
```css
/* CORRECT - Standard Tailwind v3 imports */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* WRONG - Dynamic class construction */
className={`text-${color}-500`} // Never do this!

/* CORRECT - Complete classes */
className={agentColors[agentIndex]} // Pre-defined complete classes
```

### Component Development Pattern
```typescript
// CORRECT - Using CVA for variants
import { cva } from "class-variance-authority"

const agentCardVariants = cva(
  "rounded-lg border p-4 transition-all",
  {
    variants: {
      streaming: {
        true: "border-l-4 animate-pulse",
        false: ""
      },
      selected: {
        true: "ring-2 ring-offset-2",
        false: "hover:shadow-md"
      }
    }
  }
)

// WRONG - Conditional string concatenation
className={`card ${streaming ? 'streaming' : ''} ${selected ? 'selected' : ''}`}
```

### Design System Compliance
- Read `frontend/DESIGN-SYSTEM.md` before creating new components
- Use defined color palette and spacing scale
- Follow component composition patterns
- Maintain consistency with existing UI components

### Required Secrets Before Deployment
```bash
kubectl create secret generic openai-secret \
  --from-literal=api-key="$OPENAI_API_KEY" \
  -n aideator
```

### Streaming Pipeline Architecture (Database-based)

**Current Architecture**: Hybrid PostgreSQL + WebSocket streaming for reliability and real-time capabilities.

**Current Flow**:
1. **Agent Side**:
   - Writes outputs to `agent_outputs` table via `DatabaseService`
   - Logs all agent activity (stdout, stderr, logging, status, summary, diffs, addinfo)
   - Falls back to stdout if database unavailable
   - Uses Redis for real-time message queuing

2. **Backend Side**:
   - **WebSocket Handler**: Manages real-time connections at `/ws/runs/{run_id}`
   - **Database Polling**: Fallback mechanism for message delivery
   - **Message Routing**: Routes by `variation_id` to appropriate WebSocket clients
   - **Auto-reconnect**: Handles client disconnections gracefully

3. **Frontend Side**:
   - **WebSocket Client**: Connects to `/ws/runs/{run_id}` for real-time streaming
   - **Tabbed Interface**: Multiple agent variations displayed in tabs with agent color coding
   - **Message Handling**: Routes messages by `variation_id` to appropriate tab
   - **Reconnection Logic**: Automatic reconnect with message ID tracking for resume
   - **Responsive Design**: Adapts from 1-6 agent tabs based on screen size

**Database Tables**:
- **`runs`**: Run metadata, status, configuration, user info, timestamps
- **`agent_outputs`**: Persistent storage of all agent messages with output_type classification
- **Redis**: Temporary real-time message passing and pub/sub for WebSocket delivery

### Common Pitfalls
- Always use timeout when testing WebSocket endpoints
- Don't use kubectl port-forward when Tilt is running
- Wait 10+ seconds for Tilt rebuilds
- Use complete Tailwind class names (no interpolation)
- Create openai-secret before first deployment
- PostgreSQL is REQUIRED - agents will fail without database connection
- Monitor `agent_outputs` table when debugging streaming issues
- Verify both kubectl logs AND database outputs show same data
