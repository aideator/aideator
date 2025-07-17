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
- **Parallel exploration**: Launch multiple searches/investigations simultaneously
- **Evidence-driven**: Gather data from multiple sources concurrently
- **Clean, straightforward solutions**: Build simple and clear
- **Efficient discovery**: Use parallel Tasks to explore different hypotheses
- **Uncertainty-aware**: When uncertain, explore multiple paths in parallel

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

### Debugging Protocol (With Parallel Exploration)

1. **Foundation Check**: Verify config, environment, imports
   - Launch parallel searches for related configs, dependencies, and usage patterns
2. **Evidence Collection**: Document what you observe vs. expect
   - Use multiple Task tools to gather evidence from different angles simultaneously
3. **Structured Analysis**: Use table format for problems/evidence/fixes
   - Explore multiple hypotheses in parallel when root cause unclear
4. **Simplest Correct Fix**: Most straightforward solution that properly addresses the issue
   - Test multiple potential fixes in parallel when appropriate

### Parallel Search Strategy

**When to use parallel Task tools:**
- **Pattern Discovery**: Search for class definitions, usages, and tests simultaneously
- **Error Investigation**: Check logs, configs, and code patterns in parallel
- **Refactoring**: Find all references, implementations, and tests at once
- **Architecture Understanding**: Explore models, APIs, and services concurrently

**Example parallel investigations:**
```
# When user asks "where is X implemented?"
- Task 1: Search for class/function definition
- Task 2: Search for imports and usages
- Task 3: Search for tests
- Task 4: Search for configuration references

# When debugging an error:
- Task 1: Search for error message in codebase
- Task 2: Find similar error patterns
- Task 3: Check recent changes to related files
- Task 4: Search for configuration that might affect behavior
```

**Benefits of parallel exploration:**
- Faster discovery of interconnected issues
- More comprehensive understanding of codebase
- Reduced back-and-forth investigation
- Better context for making decisions

### Confidence Check

Before any suggestion that changes dependencies, environment, or tools:
- Rate your confidence this will solve the root problem (1-10)
- If <8, don't suggest it. Ask for guidance instead

---

## 📱 Project Overview

**AIdeator** - A simplified GitHub Actions-like AI orchestration platform focused on ease of development and local deployment.

### 🎯 Core Use Case: GitHub Actions Pattern
- **Submit AI Tasks**: Like GitHub Actions workflows, submit coding tasks to AI agents
- **Background Processing**: Tasks run in containers, output streamed to database
- **Monitor Progress**: Web UI shows real-time agent outputs and final results
- **Local First**: Optimized for local development with simple deployment

### 🔄 Simplified Architecture Philosophy

**Defending Simplicity Over Complexity**:
- **Single Database**: PostgreSQL for everything (jobs, outputs, configuration)
- **Minimal Tables**: Focus on `runs` table with embedded JSON for flexibility
- **Local Development**: Optimized for student/developer environments
- **Container Orchestration**: Podman for local, Kubernetes for cloud deployment
- **Embedded Web UI**: Single integrated interface, no complex multi-service architecture

---

## 💻 Tech Stack

### Backend (FastAPI + PostgreSQL)
- **API Framework**: FastAPI with async/await patterns
- **Database**: PostgreSQL 15 with simplified schema (runs-focused)
- **Migrations**: Alembic for database schema management
- **Authentication**: Simple JWT with development bypass mode
- **Container Runtime**: Podman for local development, Kubernetes for cloud
- **Package Management**: uv for fast Python dependency management

### Frontend (Next.js 15.2.4)
- **Framework**: Next.js 15.2.4 with React 19, TypeScript 5
- **Styling**: Tailwind CSS v3.4.17 (complete classes only, no dynamic interpolation)
- **Component Library**: shadcn/ui implementation with Radix UI primitives
- **State Management**: React hooks with real-time polling
- **Integration**: Embedded in FastAPI for single-service deployment

### Agent Runtime (Simplified)
- **Execution**: Containerized agents with stdio capture
- **Providers**: Claude CLI, OpenAI, Anthropic via environment variables
- **Output Streaming**: Direct database writes with real-time web polling
- **Isolation**: Each agent runs in separate container with resource limits

### Container Orchestration Strategy
- **Local Development**: Podman for simplicity and rootless operation
- **Cloud Deployment**: Kubernetes for scalability and orchestration
- **Configuration**: XDG-compliant config directories and .env files
- **Networking**: Simplified port mapping to avoid "network hell"

### 🚨 DEPLOYMENT CRITICAL
- **ONLY use Tiltfile for deployment** - this is the single source of truth
- **NEVER suggest Helm charts or files in `/deprecated/infra/`** - these are deprecated
- All Kubernetes orchestration goes through the Tiltfile at project root

---

## 🗄️ Simplified Data Architecture

### Database Strategy: PostgreSQL-First
- **Primary Table**: `tasks` - Contains job metadata, configuration, and status
- **Task Outputs**: Stored as JSON in `tasks.outputs` or separate `task_outputs` table
- **Configuration**: API keys and settings in environment variables or XDG config
- **Persistence**: PostgreSQL for all data, SQLite for testing/development

### Container Database Considerations
- **PostgreSQL**: Production-ready, handles concurrent access
- **SQLite**: Simple for development, file-based storage
- **Data Directories**: XDG-compliant paths for configuration and data
- **Backup Strategy**: Simple file-based backups for development

### API Key Management (.env Local Approach)
```bash
# Development (.env.local)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
SIMPLE_DEV_MODE=true

# Production (XDG config)
~/.config/aideator/config.yaml
~/.local/share/aideator/data/
```

---

## 🎯 Simplification Plan

### Moving from Complex Multi-Table to Unified Tasks System
**Previous Complex Architecture**:
- Multiple tables: runs, sessions, users, provider_keys, model_definitions
- Complex relationships and foreign keys
- Over-engineered for student project needs

**Current Unified Architecture**:
- **Primary Table**: `tasks` with embedded JSON for flexibility (unified task system complete)
- **User Management**: Simple or optional (development mode)
- **API Keys**: Environment variables or XDG config files
- **Model Config**: Embedded in task configuration, not separate tables

### Database Migration Strategy
1. **Phase 1**: Preserve existing tables, add simplified alternatives
2. **Phase 2**: Migrate data to simplified schema
3. **Phase 3**: Remove complex tables once migration verified
4. **Rollback**: Always preserve original schema in comments

### Container Orchestration: Podman vs Kubernetes
**Local Development (Podman)**:
- Rootless containers for security
- Simple pod definitions
- No cluster complexity
- Direct port mapping

**Cloud Deployment (Kubernetes)**:
- Full orchestration capabilities
- Horizontal scaling
- Service mesh integration
- Production monitoring

### Development Philosophy: Defend Simplicity
**Complexity Creep Prevention**:
- **STOP Rule**: Before adding new tables/services, justify necessity
- **Question Everything**: "Can this be a simple JSON field instead?"
- **Student First**: If a CS student can't understand it in 10 minutes, simplify
- **Local Development**: Optimize for laptop development, not enterprise scale

---

## 🔧 Essential Commands

```bash
# Local Development (Podman)
podman-compose up                    # Start all services locally
podman-compose down                  # Stop all services
podman pod ps                        # List running pods

# Development with Tilt (Kubernetes)
tilt up                             # Start full k8s dev environment
tilt down                           # Stop environment
tilt trigger database-migrate       # Run database migrations

# Database Management
uv run alembic upgrade head         # Apply latest migrations
uv run alembic revision --autogenerate -m "description"  # Create migration

# Agent Testing
./scripts/test-agent-local.sh       # Test agent locally with Podman
./scripts/test-agent-k8s.sh         # Test agent in Kubernetes

# Environment Validation
uv run python scripts/validate_environment.py  # Check all dependencies
```

---

## 📁 Simplified Project Structure

```
app/                    # FastAPI backend
  api/v1/              # API routes
    tasks.py          # Core job management (primary endpoint)
    health.py         # Health check
  models/              # SQLModel database models
    task.py          # Primary model with embedded JSON
  services/            # Business logic
    agent_service.py  # Agent execution and management
    database.py       # Database connection and utilities
  
frontend/              # Next.js frontend (embedded)
  components/          # React components
  pages/               # Simple page structure
  
agent/                 # Agent container code
  main.py             # Agent entrypoint
  providers/          # LLM provider implementations
  
config/               # Configuration management
  settings.py         # Centralized settings
  
scripts/              # Utility scripts
  setup-development.sh # Interactive setup
  validate_environment.py # Environment validation
  
deploy/               # Deployment configurations
  podman/             # Podman pod definitions
  k8s/                # Kubernetes YAML files
  
tests/                # Test suite
```

---

## 🚀 Installation Strategy: "Installed Package" Approach

### XDG-Compliant Configuration
```bash
# Configuration
~/.config/aideator/
  config.yaml         # Main configuration
  api-keys.env        # Encrypted API keys
  
# Data directories
~/.local/share/aideator/
  data/              # Database files
  logs/              # Application logs
  cache/             # Temporary files
```

### Installation Methods
1. **Development**: Git clone + local setup
2. **User Install**: pip install with XDG compliance
3. **System Install**: Package manager integration
4. **Container**: Docker/Podman with volume mounts

### Configuration Hierarchy
1. Command line arguments
2. Environment variables
3. `.env.local` (development)
4. XDG config files
5. Default values

---

## 🌐 Frontend Integration: Single Embedded Web UI

### Simplified Frontend Architecture
- **Single Service**: FastAPI serves both API and web UI
- **Embedded Static Files**: Next.js build embedded in FastAPI
- **Real-time Updates**: Server-sent events or polling (no WebSockets)
- **Simple State**: React hooks with local state management

### Port Configuration
```bash
# Development
Frontend (dev):  http://localhost:3000  # Next.js dev server
API + Frontend:  http://localhost:8000  # FastAPI with embedded UI

# Production
Single Service:  http://localhost:8000  # FastAPI serves everything
```

### Networking: Simplified Approach
- **Local Development**: All services on localhost with different ports
- **Production**: Single port with path-based routing
- **No Service Mesh**: Avoid complex networking configurations
- **Direct Database**: No connection pools or complex database setups

---

## 🎓 Student-Friendly Development

### Development Philosophy
- **10-Minute Setup**: From git clone to running application
- **Minimal Dependencies**: Only essential tools required
- **Clear Error Messages**: Helpful debugging information
- **Documentation**: Every component documented with examples

### Development Workflow
1. **Clone Repository**: `git clone` and `cd aideator`
2. **Run Setup**: `./setup-development.sh` (interactive configuration)
3. **Start Services**: `podman-compose up` or `tilt up`
4. **Test Everything**: `./scripts/validate_environment.py`
5. **Submit First Task**: Use web UI at http://localhost:8000

### Debugging Support
- **Validation Scripts**: Comprehensive environment checking
- **Logging**: Structured logs with clear error messages
- **Health Checks**: API endpoints for service status
- **Development Mode**: Bypass authentication and complex features

---

## 🔍 Common Pitfalls & Solutions

### Container Orchestration Pitfalls
- **"Network Hell"**: Use simple port mapping, avoid complex networking
- **Permission Issues**: Use rootless containers (Podman) for development
- **Resource Limits**: Set appropriate CPU/memory limits for laptops
- **Storage**: Use persistent volumes for database data

### Database Strategy Pitfalls
- **Over-normalization**: Prefer JSON fields over complex relationships
- **Migration Complexity**: Keep migrations simple and reversible
- **Connection Pooling**: Not needed for development, optional for production
- **Backup Strategy**: Simple file-based backups for development

### API Key Management Pitfalls
- **Security vs Simplicity**: Use environment variables for development
- **Key Rotation**: Simple manual process for development
- **Provider Abstraction**: Don't over-engineer, use direct provider APIs
- **Rate Limiting**: Handle at provider level, not application level

---

## 📚 Key Resources

### Service URLs
- **Single Service**: http://localhost:8000 (API + Web UI)
- **Database**: localhost:5432 (PostgreSQL) or sqlite:///data/aideator.db
- **Development**: http://localhost:3000 (Next.js dev server)

### Configuration Files
- **Main Config**: `config/settings.py` (Python) or `~/.config/aideator/config.yaml`
- **API Keys**: `.env.local` (development) or `~/.config/aideator/api-keys.env`
- **Database**: Connection string in environment variables

### Documentation
- **Setup Guide**: `docs/SETUP.md` (comprehensive setup instructions)
- **Architecture**: `docs/ARCHITECTURE.md` (simplified architecture decisions)
- **API Reference**: http://localhost:8000/docs (FastAPI auto-generated docs)

---

## 💬 Communication Style

End every conversation turn with a Yoda phrase for wisdom and levity:
- "Simple, the path to wisdom is."
- "Complexity, the enemy of understanding it becomes."
- "Do or do not, there is no try."

---

## 🚨 AIdeator-Specific Gotchas

### Tailwind CSS v3 Enforcement
```typescript
// CORRECT - Complete classes only
const agentColors = {
  1: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
  2: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20'
}

// WRONG - Dynamic interpolation
className={`text-${color}-500`} // Never do this!
```

### Simplicity Enforcement
- **New Tables**: Justify why JSON in `runs` table isn't sufficient
- **New Services**: Explain why single FastAPI service isn't adequate
- **New Dependencies**: Demonstrate clear necessity over existing solutions
- **Complex Patterns**: Prefer simple, readable code over clever abstractions

### Development Mode Features
- **Authentication Bypass**: `SIMPLE_DEV_MODE=true` for development
- **Global API Keys**: Use environment variables instead of per-user keys
- **Simplified Database**: SQLite for quick development, PostgreSQL for production
- **Single Service**: No microservices complexity for development

Simple and powerful, the best architecture is. Complex solutions, the dark side they lead to.