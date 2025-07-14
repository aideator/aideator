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

**AIdeator** - A Kubernetes-native multi-agent AI orchestration platform with **decoupled background processing architecture**
- **Background Processing**: Submit tasks → agents run independently → monitor progress separately
- **Architecture Pattern**: Mirrors OpenAI Codex background agents and Cursor.com autonomous workflows
- Runs multiple AI agents in parallel in isolated containers
- Streams agent outputs to PostgreSQL for reliable task monitoring
- Enables side-by-side comparison of different AI approaches
- Cloud-native scalability with standard Kubernetes tooling

### 🔄 Decoupled Workflow Architecture

**Similar to OpenAI Codex & Cursor.com Background Processing:**

1. **Task Submission** (Main Page):
   ```
   User Input → POST /api/v1/runs → Database → Kubernetes Jobs → Background Processing
   ```

2. **Background Processing**:
   ```
   K8s Jobs → Write to SQL (agent_outputs) → Continue independently
   ```

3. **Task Monitoring** (Task Detail Page):
   ```
   User Navigation → GET /api/v1/tasks/{id} → Read SQL → Display Progress
   ```

**Key Benefits:**
- Submit work and get immediate acknowledgment
- Jobs run completely independently in background
- Monitor progress later via separate interface
- All communication flows through PostgreSQL for reliability
- No frontend blocking or WebSocket dependencies

---

## 💻 Tech Stack

### Frontend (Next.js 15.2.4)
- **Framework**: Next.js 15.2.4 with React 19, TypeScript 5
- **Navigation**: Next.js App Router with simplified page structure
- **Styling**: Tailwind CSS v3.4.17 (complete classes only, no dynamic interpolation)
- **Component Library**: Full shadcn/ui implementation with Radix UI primitives
- **Design System**: Comprehensive AIdeator design system (see frontend/DESIGN-SYSTEM.md)
- **Icons**: Lucide React v0.454.0 for consistent iconography
- **State Management**: React hooks with custom hooks (use-agent-logs, use-tasks, use-toast)
- **Forms**: React Hook Form v7.54.1 with Zod validation
- **Charts**: Recharts v3.1.0 for data visualization
- **Theming**: next-themes v0.4.4 for dark/light mode support
- **Animation**: tailwindcss-animate v1.0.7 with streaming animations
- **Dialogs**: Vaul v1.1.2 for mobile-optimized drawers
- **Testing**: Jest v30.0.4 + Testing Library v16.3.0 (unit), Playwright v1.54.1 (E2E)
- **Code Quality**: ESLint, TypeScript v5 strict mode, Knip v5.61.3 for dead code detection

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

### Agent Runtime (Refactored Architecture)
- **Orchestration**: Modular `AgentOrchestrator` with clean separation of concerns
- **LLM Providers**: Multiple provider implementations:
  - `ClaudeCLIProvider` - Claude CLI integration
  - `LiteLLMCLIProvider` - LiteLLM CLI with subprocess pattern
  - `GeminiCLIProvider` - Google Gemini CLI integration
- **Repository Analysis**: `RepositoryAnalyzer` and `CodebaseAnalyzer` modules
- **Output Streaming**: `DatabaseService` for PostgreSQL persistence + `OutputWriter` for real-time logging
- **Configuration**: Centralized settings via `config/settings.py` and `config/providers.py`
- **Container Isolation**: Each agent variation runs in isolated Kubernetes Jobs with resource limits

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

# Environment Validation (NEW - Decoupled Architecture)
uv run python scripts/check_everything.py    # Comprehensive environment validation
uv run python scripts/validate_dev_environment.py  # Core validation only
uv run python scripts/test_api_endpoints.py         # Test decoupled API architecture

# Database Management
uv run alembic upgrade head   # Apply latest migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
python -m scripts.add_test_data  # Seed test data

# Agent Container Management (NEW - Force Rebuild)
./force-rebuild-agent.sh     # Clean, rebuild, push agent container to k3d registry

# Testing Background Processing Workflow (NEW)
# Submit task (like OpenAI Codex "Run" button)
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"github_url":"https://github.com/fastapi/fastapi","prompt":"Test task","model_variants":[{"model_definition_id":"gpt-4o-mini"}],"agent_mode":"litellm"}'

# Monitor tasks (like Cursor.com background status)
curl http://localhost:8000/api/v1/tasks
curl http://localhost:8000/api/v1/tasks/{task_id}
curl http://localhost:8000/api/v1/tasks/{task_id}/outputs

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

## 🎓 Student-Friendly Tilt Setup (NEW)

**IMPORTANT**: We've replaced complex Helm charts with simple Kubernetes YAML files for easier student development.

### New Tilt Architecture
- **No Helm complexity** - Uses simple `k8s/*.yaml` files instead
- **Automatic port forwarding** - All services available on localhost
- **Manual migration control** - Run migrations when you need them
- **Student development mode** - Authentication bypass enabled by default

### Port Forwarding (Automatic)
```bash
# All services are automatically port-forwarded by Tilt:
Frontend:  http://localhost:3000  # (runs locally, not in k8s)
API:       http://localhost:8000  # (k8s service forwarded)
Database:  localhost:5432         # (k8s service forwarded)
Redis:     localhost:6379         # (k8s service forwarded)
LiteLLM:   http://localhost:4000  # (k8s service forwarded)
API Docs:  http://localhost:8000/docs
Tilt UI:   http://localhost:10350
```

### Database Setup
```bash
# Database migration is MANUAL now (no auto-init)
tilt trigger database-migrate     # Run this ONCE after `tilt up`

# The migration connects to port-forwarded database:
# postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator
```

### Student Mode Features (Auto-Enabled)
- `SIMPLE_DEV_MODE=true` - Bypass complex authentication
- `AUTO_CREATE_TEST_USER=true` - Test user created automatically
- `REQUIRE_API_KEYS_FOR_AGENTS=false` - No API key required for endpoints
- Global API keys used from `.env.local` file

### Tilt File Locations
```
Tiltfile                    # Main Tilt configuration (student-friendly)
k8s/database.yaml          # PostgreSQL deployment (simple YAML)
k8s/redis.yaml             # Redis deployment (simple YAML) 
k8s/litellm.yaml           # LiteLLM gateway (simple YAML)
k8s/api.yaml               # API deployment with student mode env vars
k8s/rbac.yaml              # Kubernetes permissions for agent jobs
```

### Key Differences from Helm Version
- ✅ **Simple YAML** instead of Helm templates
- ✅ **Predictable port forwarding** (localhost:5432, :8000, etc.)
- ✅ **Manual migration trigger** instead of auto-init jobs
- ✅ **Student mode enabled** by default in all deployments
- ✅ **No complex values.yaml** - everything in simple k8s YAML

---

## 📁 Project Structure

```
app/                    # FastAPI backend
  api/v1/              # API routes
    auth.py           # Authentication endpoints
    runs.py           # Task creation and management
    tasks.py          # Task monitoring and progress
    sessions.py       # Session management
    agent_outputs.py  # Agent output streaming
    admin_messaging.py # Admin messaging
    credentials.py    # Credential management
    health.py         # Health check endpoints
    models.py         # Model management
    preferences.py    # User preferences
    websocket.py      # WebSocket connections
    endpoints/        # Specialized endpoints (admin.py, provider_keys.py)
  core/                # Core services (config, database, dependencies, logging)
  middleware/          # Custom middleware
    development.py    # Development auth bypass
    logging.py        # Request logging
    rate_limit.py     # Rate limiting
  models/              # SQLModel database models
    run.py           # Run/task model
    session.py       # Session model
    user.py          # User model
    provider_key.py  # Encrypted API key model
    model_definition.py # Model definitions
    provider.py      # Provider configurations
  schemas/             # Pydantic schemas
    auth.py          # Authentication schemas
    common.py        # Common schemas
    runs.py          # Run/task schemas
    session.py       # Session schemas
    tasks.py         # Task monitoring schemas
    models.py        # Model schemas
  services/            # Business logic services
    agent_orchestrator.py      # Agent orchestration
    auth_service.py           # Authentication service
    database_init.py          # Database initialization
    encryption_service.py     # Key encryption
    global_key_service.py     # Global API key management
    kubernetes_service.py     # Kubernetes job management
    litellm_model_discovery.py # LiteLLM model discovery
    model_catalog.py          # Model catalog management
    model_discovery_service.py # Model discovery
    model_sync_service.py     # Model synchronization
    provider_key_service.py   # Provider key management
    redis_service.py          # Redis integration
  tasks/               # Background tasks (model_sync_task.py)
  utils/               # Utilities (github.py, openapi.py)
  
frontend/              # Next.js 15 frontend (new simplified structure)
  app/                 # App Router pages (main page, session pages, test pages)
  components/          # React components (ui/, agent-output-viewer, theme-provider)
  hooks/               # Custom React hooks (use-agent-outputs, use-tasks, use-toast)
  lib/                 # Utilities (data, utils)
  
frontend-old/          # Legacy frontend (complex multi-agent UI)
  
agent/                 # AI agent container code (refactored modular architecture)
  main.py              # Agent entrypoint with AIdeatorAgent class
  main_wrapper.py      # Async wrapper for container execution
  analyzers/           # Codebase analysis modules (codebase.py, repository.py)
  config/              # Configuration management
    settings.py        # Main configuration settings
    providers.py       # Provider-specific configurations
  core/                # Core orchestration logic
    orchestrator.py    # Main AgentOrchestrator class
  providers/           # LLM provider implementations
    base.py           # Base provider interface
    claude_cli.py     # Claude CLI provider
    litellm_cli.py    # LiteLLM CLI provider (new)
    gemini_cli.py     # Google Gemini CLI provider
    subprocess_base.py # Base subprocess provider pattern
  services/            # Core services
    database_service.py # PostgreSQL persistence service
    output_writer.py   # Real-time output logging
    redis.py          # Redis service integration
  utils/               # Utility functions (errors.py, files.py)
  scripts/             # Helper scripts (litellm_wrapper.py)
  
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
- **Persistent Database**: PostgreSQL data stored in `/tmp/aideator-postgres-data` - survives `tilt down`

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

### 🔗 Service URLs
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (comprehensive endpoint documentation)
- **LiteLLM Gateway**: http://localhost:4000
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432
- **Tilt UI**: http://localhost:10350

### 📋 Validation Scripts (NEW)
- **`scripts/check_everything.py`**: Comprehensive environment validation with background workflow simulation
- **`scripts/validate_dev_environment.py`**: Core environment validation (database, API, Kubernetes)
- **`scripts/test_api_endpoints.py`**: Test decoupled API architecture (runs vs tasks)

### 📖 Architecture Documentation
- **`TASK-RUN-ARCHITECTURE.md`**: Decoupled background processing architecture
- **`CLAUDE.md`**: This development guide
- **`frontend/DESIGN-SYSTEM.md`**: UI component guidelines
- **`frontend/CLAUDE.md`**: Frontend-specific development notes

### 🏗️ Infrastructure
- **Kubernetes Namespace**: `aideator` (all resources)
- **Local Registry**: `localhost:5005` (for container images)
- **Student Mode**: Simple dev setup without Helm complexity

### 🔍 Background Processing References
- **OpenAI Codex**: Background coding agents in ChatGPT interface
- **Cursor.com**: Autonomous background code generation workflows  
- **Pattern**: Submit → Background Process → Monitor Progress independently

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

### Decoupled Background Processing Architecture

**Architecture**: PostgreSQL-first with decoupled task submission and monitoring (like OpenAI Codex/Cursor.com).

**Decoupled Flow**:
1. **Task Submission** (Main Page):
   - Frontend calls `POST /api/v1/runs` with task details
   - Creates entry in `runs` table
   - Spawns Kubernetes Jobs for background processing
   - Returns immediately with task ID

2. **Background Processing** (Independent):
   - **Agent Containers**: Write outputs to `agent_outputs` table via `DatabaseService`
   - **Output Types**: stdout, stderr, logging, status, summary, diffs, addinfo, metrics
   - **Isolation**: Each variation runs in separate container
   - **Persistence**: All communication flows through PostgreSQL

3. **Task Monitoring** (Task Detail Page):
   - Frontend calls `GET /api/v1/tasks` for task list
   - Calls `GET /api/v1/tasks/{id}` for specific task details  
   - Calls `GET /api/v1/tasks/{id}/outputs` for agent progress
   - **Polling**: Frontend polls outputs endpoint for real-time updates
   - **Variation Comparison**: Tabbed interface shows multiple agent approaches

**API Separation**:
- **`/api/v1/runs`**: Task creation and Kubernetes job management
- **`/api/v1/tasks`**: Task monitoring and progress tracking
- **Task ID = Run ID**: Simplified identifier mapping

**Database Tables**:
- **`runs`**: Task metadata, configuration, Kubernetes job status
- **`agent_outputs`**: All agent communication and results (central hub)
- **Redis**: Optional for real-time WebSocket streaming (not required for core functionality)

### Common Pitfalls (Decoupled Architecture)
- **API Confusion**: Use `/api/v1/runs` for task creation, `/api/v1/tasks` for monitoring
- **Task ID = Run ID**: They're the same identifier, simplifies data model
- **Database First**: All agent communication flows through PostgreSQL, not Redis/WebSocket
- **Polling vs Streaming**: Task detail page polls `/tasks/{id}/outputs` for updates
- **Authentication**: Simple dev mode bypasses auth - check `SIMPLE_DEV_MODE=true`
- **Background Jobs**: Kubernetes jobs run independently, may take time to start
- **Status Tracking**: We don't monitor job completion yet - infer from agent outputs
- **Frontend Separation**: Main page (task submission) ≠ Task detail page (monitoring)
- **PostgreSQL Required**: Agents fail without database connection - verify with validation scripts
- **Complete Tailwind Classes**: No dynamic class interpolation allowed
