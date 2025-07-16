# AIdeator

**Simple multi-agent AI comparison platform for coding tasks**

AIdeator enables side-by-side comparison of different AI approaches to the same coding task. Built with a student-friendly development philosophy, it prioritizes simplicity and quick setup over architectural complexity. Think GitHub Actions for AI agents - submit a task, agents run in containers, view results.

## 🚀 Key Features

### Simple Multi-Agent Comparison
- **2-Page Frontend**: Submit tasks → View results (no complex navigation)
- **3-Endpoint API**: POST /runs, GET /runs/{id}, GET /runs/{id}/outputs
- **Container Execution**: Agents run in isolated containers (Podman locally, Kubernetes in cloud)
- **Side-by-Side Results**: Compare different AI approaches and implementations

### GitHub Actions-Like Workflow
- **Submit & Go**: Submit coding tasks and agents run in background
- **Job Execution**: Each agent runs as an independent container job
- **Progress Monitoring**: Real-time logs and outputs via database polling
- **Multiple Providers**: Support for OpenAI, Anthropic, and other LLM providers

### Student-Friendly Development
- **10-Minute Setup**: Simple installation with minimal complexity
- **XDG-Compliant Storage**: Data stored in standard system directories
- **Daemon Management**: Proper start/stop/restart commands
- **Single Database**: PostgreSQL for everything (no Redis complexity)

## 🔄 Simplified Architecture

### Core Components
- **Frontend**: 2 pages (Submit + Results)
- **API**: 3 endpoints (create run, get run, get outputs)
- **Database**: Single PostgreSQL instance
- **Containers**: Podman (local) or Kubernetes (cloud)

### Workflow
```
1. Submit Task → POST /api/v1/runs → Database Entry → Container Job
2. Monitor Progress → GET /api/v1/runs/{id}/outputs → Database → Display
```

### Data Flow
- **Single Table**: `runs` table stores everything
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

## 🎯 Core Use Case: Multi-Agent Comparison

### Simple 2-Page Workflow
1. **Submit Page** (`http://localhost:3000`)
   - Enter GitHub repository URL and coding prompt
   - Select AI models to compare (GPT-4, Claude, etc.)
   - Submit task → Container jobs start in background

2. **Results Page** (`http://localhost:3000/runs/{id}`)
   - View side-by-side outputs from different AI models
   - Compare approaches, code changes, and reasoning
   - All outputs captured in real-time via database polling

### What You Get
- **Different AI Perspectives**: See how GPT-4 vs Claude approaches the same task
- **Code Comparison**: View proposed changes side-by-side
- **Execution Logs**: Full transparency into AI reasoning process
- **Error Analysis**: Understand where different models succeed/fail

### Container Execution
- **Isolated Jobs**: Each AI model runs in separate container
- **Resource Limits**: Prevents runaway processes
- **Automatic Cleanup**: Containers terminate after completion
- **Progress Tracking**: Real-time status via database

## 🔧 Development Commands

```bash
# Environment Management
tilt up                        # Start full development environment
tilt down                     # Stop all services
tilt trigger database-migrate  # Run database migrations

# Testing & Validation
uv run python scripts/check_everything.py    # Full environment validation
uv run python scripts/test_api_endpoints.py  # API architecture testing

# Container Management
./force-rebuild-agent.sh     # Force rebuild agent containers

# Code Quality
uv run test-all              # Run all tests and quality checks
cd frontend && npm run test  # Frontend tests
```

## 📊 Monitoring & Observability

### Service Health
- **API Health**: `http://localhost:8000/health`
- **Database**: PostgreSQL with persistent storage
- **Redis**: Optional for enhanced streaming
- **Kubernetes**: Job status and resource monitoring

### Logging & Metrics
- **Structured logging** with request IDs
- **Prometheus metrics** for monitoring
- **Database persistence** of all agent outputs
- **Real-time streaming** via WebSocket connections

## 🌟 Use Cases

### Code Analysis
- **Repository analysis** with multiple AI perspectives
- **Code review** automation with different models
- **Documentation generation** comparison

### Development Workflow
- **Prototype comparison** - see different implementation approaches
- **Model evaluation** - compare AI model performance on coding tasks
- **Educational tool** - understand different AI reasoning patterns

### Research & Development
- **Multi-model benchmarking** on coding tasks
- **Prompt engineering** with side-by-side results
- **AI behavior analysis** across different providers

## 🔒 Security & Production

### Development Mode
- **Global API keys** for simplified development
- **Authentication bypass** for local testing
- **Persistent database** storage in `/tmp`

### Production Considerations
- **Per-user API key management** with encryption
- **Full authentication** system with JWT tokens
- **Distributed storage** and backup strategies
- **Resource limits** and monitoring

## 🤝 Contributing

### Development Workflow
1. **Read** `CLAUDE.md` for detailed development guidelines
2. **Follow** the student-friendly Tilt setup
3. **Test** changes with validation scripts
4. **Submit** pull requests with comprehensive testing

### Code Quality
- **TypeScript strict mode** for frontend
- **Ruff formatting** for Python backend
- **Comprehensive testing** with pytest and Jest
- **Database migrations** for schema changes

## 📚 Documentation

- **`CLAUDE.md`** - Comprehensive development guide
- **`TASK-RUN-ARCHITECTURE.md`** - Background processing architecture
- **`frontend/DESIGN-SYSTEM.md`** - UI component guidelines
- **API Documentation** - Available at `http://localhost:8000/docs`

## 🎓 Educational Focus

AIdeator is designed as a **student-friendly** project with:
- **Simple Kubernetes setup** using k3d and Tilt
- **Clear documentation** with step-by-step guides
- **Comprehensive validation** scripts
- **Real-world patterns** for cloud-native development

---

*Built with modern cloud-native principles for reliable, scalable AI agent orchestration*