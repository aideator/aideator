# AIdeator

**Background pipeline for AI-assisted development**

AIdeator is a development pipeline that runs AI agents in the background while you continue coding. Built with a student-friendly development philosophy, it prioritizes simplicity and quick setup over architectural complexity. Think CI/CD for AI assistance - submit tasks to the pipeline, keep working while agents process in parallel, check results when convenient.

## 🚀 Key Features

### AI Development Pipeline
- **Fire-and-Forget**: Submit development tasks to the pipeline and continue coding
- **Background Processing**: AI agents work asynchronously while you focus on other tasks
- **Parallel Execution**: Multiple agents explore different implementation approaches simultaneously
- **Pipeline Observability**: Monitor agent progress when convenient through simple web interface

### Asynchronous Development Workflow
- **Pipeline Submission**: POST tasks to the pipeline, get immediate acknowledgment
- **Background Agents**: Each agent runs in isolated containers processing independently
- **Progress Monitoring**: Check pipeline status and outputs via database polling
- **Multiple Providers**: Leverage OpenAI, Anthropic, and other LLMs in parallel

### Student-Friendly Development
- **10-Minute Setup**: Simple installation with minimal complexity
- **XDG-Compliant Storage**: Data stored in standard system directories
- **Daemon Management**: Proper start/stop/restart commands
- **Single Database**: PostgreSQL for everything (no Redis complexity)

## 🔄 Simplified Architecture

### Core Components
- **Frontend**: 2 pages (Submit + Results)
- **API**: 3 endpoints (create task, get task, get outputs)
- **Database**: Single PostgreSQL instance
- **Containers**: Podman (local) or Kubernetes (cloud)

### Workflow
```
1. Submit Task → POST /api/v1/tasks → Database Entry → Container Job
2. Monitor Progress → GET /api/v1/tasks/{id}/outputs → Database → Display
```

### Data Flow
- **Single Table**: `tasks` table stores everything
- **No Sessions**: Stateless operation
- **No Complex Auth**: Simple development mode
- **Container Logs**: All outputs captured in database

## 🛠️ Simplified Tech Stack

**Frontend**: Next.js 15 with React 19, TypeScript, Tailwind CSS, shadcn/ui  
**Backend**: FastAPI with PostgreSQL, SQLModel ORM  
**Agent Runtime**: Podman (local) or Kubernetes (cloud) containers  
**Development**: Simple daemon management with systemd  
**Database**: PostgreSQL only (no Redis complexity)  
**LLM Gateway**: LiteLLM for multi-provider support

## 📁 Project Structure

```
app/                    # FastAPI backend (simplified API)
frontend/              # Next.js frontend (2 pages: submit + results)
agent/                 # AI agent container code
alembic/               # Database migrations (simplified schema)
scripts/               # Setup and validation scripts
deploy/                # Installation and daemon management
```

## 🚀 Quick Start (10-Minute Setup)

### Prerequisites
- Linux/macOS system
- Python 3.11+ and Node.js 18+
- Podman or Docker installed

### Installation (Recommended)
```bash
# Clone and install as system package
git clone <repository-url>
cd aideator

# Install system-wide (creates daemons, data directories)
sudo make install

# Configure API keys
aideator config set OPENAI_API_KEY="your-openai-key"
aideator config set ANTHROPIC_API_KEY="your-anthropic-key"  # optional

# Start services
aideator start

# Access application
open http://localhost:3000  # Frontend
open http://localhost:8000  # API
```

### Development Setup (Alternative)
```bash
# Clone repository
git clone <repository-url>
cd aideator

# Run interactive setup
./setup-development.sh

# Start development environment
tilt up

# Run database migrations (one-time)
tilt trigger database-migrate
```

## 🎯 Core Use Case: Background AI Development Pipeline

### Simple Pipeline Workflow
1. **Submit to Pipeline** (`http://localhost:3000`)
   - Enter GitHub repository URL and development prompt
   - Select AI agents for parallel exploration (GPT-4, Claude, etc.)
   - Submit task → Pipeline starts processing in background

2. **Continue Working** 
   - Keep coding while AI agents process your task
   - No blocking, no waiting - pure asynchronous workflow
   - Pipeline runs independently in the background

3. **Check Pipeline Results** (`http://localhost:3000/tasks/{id}`)
   - View outputs from parallel AI agents when convenient
   - See different implementation approaches explored
   - All pipeline activity captured for full observability

### Pipeline Benefits
- **Asynchronous Development**: Submit and forget, check results later
- **Parallel Exploration**: Multiple AI agents work on your task simultaneously
- **Non-Blocking Workflow**: Continue your work while pipeline processes
- **Full Observability**: Complete visibility into pipeline execution

### Pipeline Execution
- **Isolated Processing**: Each agent runs in separate container
- **Resource Management**: Pipeline prevents runaway processes
- **Automatic Cleanup**: Pipeline manages container lifecycle
- **Progress Tracking**: Real-time pipeline status via database

## 🔧 System Management

### Installation Commands
```bash
# System-wide installation
sudo make install           # Install as system package
sudo make uninstall         # Remove installation

# Service management
aideator start              # Start all services
aideator stop               # Stop all services
aideator restart            # Restart services
aideator status             # Check service status

# Configuration
aideator config set KEY=value  # Set configuration
aideator config get KEY        # Get configuration
aideator config list          # List all settings
```

### Development Commands
```bash
# Development environment (alternative to installation)
tilt up                        # Start development environment
tilt down                     # Stop all services
tilt trigger database-migrate  # Run database migrations

# Testing & Validation
uv run python scripts/check_everything.py    # Full environment validation
uv run python scripts/test_api_endpoints.py  # API testing

# Code Quality
uv run test-all              # Run all tests and quality checks
cd frontend && npm run test  # Frontend tests
```

## 📊 Data & Storage

### Data Persistence
- **Database**: PostgreSQL stored in XDG-compliant directories
- **Configuration**: `~/.config/aideator/config.toml`
- **Logs**: `~/.local/share/aideator/logs/`
- **Container Images**: Managed by Podman/Docker

### Service Health
- **API Health**: `http://localhost:8000/health`
- **Database Status**: `aideator status database`
- **Container Status**: `aideator status containers`
- **Full Status**: `aideator status`

### Monitoring
- **Structured logging** with request IDs
- **Database-driven progress** tracking
- **Container resource** monitoring
- **Simple polling** for real-time updates (no WebSocket complexity)

## 🌟 Primary Use Cases: Pipeline-Based Development

### Core Concept
**"Submit AI development tasks to the pipeline and continue working while agents process in parallel"**

### Practical Pipeline Applications
- **Automated Refactoring**: Submit legacy code for parallel refactoring approaches while you work on features
- **Code Analysis**: Pipeline analyzes codebase for improvements while you continue development
- **Documentation Generation**: AI agents create documentation in background as you code
- **Implementation Exploration**: Explore multiple approaches to a problem without blocking your workflow

### Example Pipeline Workflows

#### Background Refactoring
1. **Submit**: "Refactor this authentication module to use JWT"
2. **Continue**: Work on other features while pipeline processes
3. **Review**: Check multiple refactoring approaches when ready
4. **Apply**: Choose the best approach or combine insights

#### Parallel Code Review
1. **Submit**: "Review this pull request for security issues"
2. **Pipeline**: Multiple AI agents analyze code independently
3. **Results**: Comprehensive security analysis ready when you need it

#### Asynchronous Documentation
1. **Submit**: "Generate API documentation for this service"
2. **Background**: Agents create docs while you keep coding
3. **Complete**: Well-documented code without interrupting flow

### Pipeline Value
- **Non-Blocking**: Never wait for AI - submit and continue working
- **Parallel Processing**: Multiple agents explore solutions simultaneously
- **Developer Flow**: Maintains coding momentum with background assistance
- **Comprehensive Results**: Get thorough analysis from parallel agent execution

## 🔒 Deployment Options

### Local Development (Default)
- **Global API keys** stored in user config
- **Simple authentication** bypass for development
- **XDG-compliant** data storage in user directories
- **Podman containers** for agent isolation

### Production Deployment
- **Kubernetes** for container orchestration
- **Per-user API key** management with encryption
- **Persistent volumes** for database storage
- **Resource limits** and monitoring
- **Proper authentication** with JWT tokens

### Security Considerations
- **Container isolation** prevents cross-contamination
- **Resource limits** prevent runaway processes
- **Database encryption** for sensitive data
- **API key management** with proper rotation

## 🤝 Development Philosophy

### Simplicity First
- **Ease of development** prioritized over architectural complexity
- **10-minute setup** goal for new developers
- **Student-friendly** patterns and documentation
- **Minimal dependencies** - only what's necessary

### Development Workflow
1. **Read** `CLAUDE.md` for detailed development guidelines
2. **Use** simple installation or development setup
3. **Test** changes with validation scripts
4. **Submit** pull requests with comprehensive testing

### Code Quality
- **TypeScript strict mode** for frontend
- **Ruff formatting** for Python backend
- **Comprehensive testing** with pytest and Jest
- **Database migrations** for schema changes
- **Container testing** with agent validation

## 📚 Documentation

- **`CLAUDE.md`** - Comprehensive development guide
- **`frontend/DESIGN-SYSTEM.md`** - UI component guidelines
- **API Documentation** - Available at `http://localhost:8000/docs`
- **Installation Guide** - `./setup-development.sh` for interactive setup

## 🎓 Educational Focus

AIdeator is designed as a **student-friendly** project with:
- **10-minute setup** from clone to running
- **Simple architecture** - no unnecessary complexity
- **Clear documentation** with step-by-step guides
- **Comprehensive validation** scripts
- **Real-world patterns** without enterprise overhead

### Key Learning Outcomes
- **API Design**: RESTful patterns with FastAPI
- **Container Orchestration**: Podman locally, Kubernetes in production
- **Database Design**: PostgreSQL with migrations
- **Frontend Development**: Modern React with TypeScript
- **AI Integration**: Multi-provider LLM orchestration

---

*Built with student-friendly simplicity for asynchronous AI development pipelines*