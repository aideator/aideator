# AIdeator

**Kubernetes-native multi-agent AI orchestration platform for background code analysis and generation**

AIdeator provides a robust, scalable infrastructure for running multiple AI coding agents in parallel, enabling side-by-side comparison of different AI approaches to the same coding task. Built with modern cloud-native principles, it offers reliable background processing similar to enterprise AI development tools.

## 🚀 Key Features

### Decoupled Background Processing
- **Submit & Monitor**: Submit coding tasks and monitor progress independently
- **Background Execution**: AI agents run autonomously in isolated Kubernetes containers
- **Reliable Persistence**: All outputs streamed to PostgreSQL for consistent monitoring
- **Real-time Updates**: Live progress tracking through database polling

### Multi-Agent Comparison
- **Parallel Processing**: Run up to 6 AI agents simultaneously on the same task
- **Side-by-Side Analysis**: Compare different AI approaches and implementations
- **Multiple Providers**: Support for OpenAI, Anthropic, and other LLM providers via LiteLLM
- **Comprehensive Outputs**: Logs, errors, diffs, and code changes captured per agent

### Cloud-Native Architecture
- **Kubernetes Jobs**: Each agent runs in an isolated container with resource limits
- **Horizontal Scaling**: Scale agents independently based on workload
- **Standard Tooling**: Built on proven Kubernetes patterns and tooling
- **Local Development**: Student-friendly k3d setup with Tilt orchestration

## 🔄 Workflow Architecture

### 1. Task Submission
```
User Input → POST /api/v1/runs → Database → Kubernetes Jobs → Background Processing
```

### 2. Background Processing
```
K8s Jobs → Write to PostgreSQL → Continue independently
```

### 3. Task Monitoring
```
User Navigation → GET /api/v1/tasks/{id} → Read Database → Display Progress
```

## 🛠️ Tech Stack

**Frontend**: Next.js 15 with React 19, TypeScript, Tailwind CSS, shadcn/ui
**Backend**: FastAPI with async/await, PostgreSQL, SQLModel ORM
**Agent Runtime**: Kubernetes Jobs with LiteLLM for multi-provider support
**Development**: Tilt + k3d for local Kubernetes development
**Infrastructure**: Docker multi-stage builds, Prometheus metrics, structured logging

## 📁 Project Structure

```
app/                    # FastAPI backend API
frontend/              # Next.js frontend application
agent/                 # AI agent container code
k8s/                   # Kubernetes deployment templates
alembic/               # Database migrations
scripts/               # Development and validation scripts
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop with Kubernetes enabled
- k3d cluster management
- Tilt for development orchestration
- Node.js 18+ and Python 3.11+

### Development Setup
```bash
# Clone and setup
git clone <repository-url>
cd aideator

# Start development environment
tilt up

# Run database migrations (one-time)
tilt trigger database-migrate

# Access services
open http://localhost:3000  # Frontend
open http://localhost:8000  # API
open http://localhost:10350 # Tilt Dashboard
```

### Environment Configuration
```bash
# Required API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # optional
```

## 🎯 Core Workflow

### Creating a Task
1. **Navigate** to the main page (`http://localhost:3000`)
2. **Enter** GitHub repository URL and coding prompt
3. **Select** number of agent variations (1-6)
4. **Submit** - task is queued for background processing
5. **Redirected** to task monitoring page

### Monitoring Progress
- **Real-time logs** from each agent variation
- **Error tracking** with detailed error analysis
- **Code diffs** showing proposed changes
- **Side-by-side comparison** of different AI approaches

### Agent Variations
Each agent runs independently in its own container:
- **Isolated execution** with resource limits
- **Different models** (GPT-4, Claude, etc.)
- **Comprehensive logging** of all actions
- **Automatic cleanup** after completion

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