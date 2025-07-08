# AIdeator 🚀

**Multi-Agent AI Orchestration Platform**

A Kubernetes-native LLM orchestration platform that runs multiple AI agents in parallel, streaming their thought processes in real-time. Compare different AI approaches side-by-side and select the best solution.

![Architecture](https://img.shields.io/badge/Architecture-Kubernetes%20Native-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Streaming](https://img.shields.io/badge/Streaming-Server%20Sent%20Events-orange)

## ✨ Features

- **🔄 Multi-Agent Orchestration**: Run 1-5 AI agents simultaneously in isolated Kubernetes Jobs
- **📡 Real-time Streaming**: Watch agent thought processes live via Server-Sent Events
- **🔍 Side-by-Side Comparison**: Compare outputs from multiple agents in responsive grid layout
- **🎨 Modern UI**: Clean, accessible interface built with Next.js and custom design system
- **☁️ Cloud-Native**: Kubernetes-native architecture with Helm charts and Tilt development
- **🔧 Developer-Friendly**: Hot reload, comprehensive logging, and GitOps-ready deployment

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Node.js 18+** and **npm**
- **kubectl** and **Helm** (for Kubernetes)
- **Tilt** (for local development)
- **Anthropic API Key** (Claude)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/aideator.git
cd aideator

# Copy environment files
cp .env.example .env

# Add your Anthropic API key to .env
echo "OPENAI_API_KEY=your-anthropic-key-here" >> .env
```

### 2. Start Development Environment

```bash
# Start the full stack with Tilt (recommended)
tilt up

# This will:
# 1. Start/verify k3d Kubernetes cluster
# 2. Build and deploy FastAPI backend
# 3. Set up port forwarding
# 4. Watch for file changes

# Services will be available at:
# - Tilt UI: http://localhost:10350
# - FastAPI Backend: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
```

### 3. Start Frontend

```bash
# In a separate terminal
cd frontend
npm install
npm run dev

# Frontend available at:
# - Next.js App: http://localhost:3000
```

### 4. Test the Application

1. **Open http://localhost:3000** - Homepage with feature overview
2. **Click "Start Multi-Agent Generation"** - Go to streaming interface
3. **Configure Task**:
   - Repository URL: `https://github.com/octocat/Hello-World`
   - Prompt: `Analyze this repository and suggest improvements`
   - Agents: `3`
4. **Click "Start Generation"** - Watch agents work in real-time!

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    HTTP/SSE     ┌─────────────────┐    kubectl logs    ┌─────────────────┐
│   Next.js       │ ───────────────▶│   FastAPI       │ ──────────────────▶│  Kubernetes     │
│   Frontend      │                 │   Backend       │                    │  Agent Jobs     │
│   (Port 3000)   │                 │   (Port 8000)   │                    │                 │
└─────────────────┘                 └─────────────────┘                    └─────────────────┘
```

### Tech Stack

**Frontend**
- **Next.js 14** with App Router and TypeScript
- **Tailwind CSS** with custom design system
- **Server-Sent Events** for real-time streaming
- **Responsive Design** (mobile to 5-column desktop)

**Backend**
- **FastAPI** with async/await patterns
- **SQLite + SQLModel** for data persistence
- **Kubernetes Jobs** for agent isolation
- **kubectl** native log streaming

**Infrastructure**
- **Kubernetes** (k3d for local development)
- **Helm Charts** for declarative deployment
- **Tilt** for local development workflow
- **Local Registry** (localhost:5005) for fast iteration

### Key Components

```
frontend/                  # Next.js application
├── app/                    # Next.js pages
│   ├── page.tsx           # Homepage
│   └── stream/page.tsx    # Multi-agent interface
├── components/
│   ├── agents/            # Agent-specific components
│   │   ├── StreamCard.tsx # Individual agent display
│   │   └── StreamGrid.tsx # Multi-agent layout
│   └── ui/                # Design system components
├── hooks/
│   └── useAgentStream.ts  # SSE streaming hook
└── lib/
    └── api.ts             # FastAPI client

app/                       # FastAPI backend
├── api/v1/               # API endpoints
├── services/             # Business logic
│   ├── kubernetes_service.py    # Job orchestration
│   ├── agent_orchestrator.py   # Multi-agent management
│   └── sse_manager.py          # Real-time streaming
└── main.py               # Application entry

deploy/
├── charts/aideator/      # Helm chart
└── values/               # Environment configs
```

## 🛠️ Development

### Local Development Workflow

```bash
# Start everything with Tilt (backend + k8s)
tilt up

# Start frontend in separate terminal
cd frontend && npm run dev

# Make changes and see live updates:
# - Frontend: Hot reload automatically
# - Backend: Tilt rebuilds in ~10 seconds
# - Agents: Touch agent/main.py to trigger rebuild
```

### Testing

```bash
# Backend tests
pytest tests/

# Frontend tests (coming soon)
cd frontend
npm test

# End-to-end tests with Playwright
npm run test:e2e

# Manual API testing
curl http://localhost:8000/api/v1/health
```

### Code Quality

```bash
# Backend linting and formatting
ruff check .
ruff format .
mypy app/

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

### Kubernetes Operations

```bash
# Check running pods
kubectl get pods -n aideator

# Stream logs from specific agent
kubectl logs -f job/agent-run123-0 -n aideator

# Debug failed jobs
kubectl describe job agent-run123-0 -n aideator

# Clean up completed jobs
kubectl delete jobs --field-selector status.successful=1 -n aideator
```

## 📡 API Usage

### Create Multi-Agent Run

```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "prompt": "Analyze this repository and suggest improvements",
    "variations": 3
  }'

# Response:
{
  "run_id": "run-abc123",
  "stream_url": "/api/v1/runs/run-abc123/stream",
  "status": "accepted"
}
```

### Stream Real-Time Output

```bash
# Stream agent outputs (use timeout to avoid hanging)
timeout 30 curl -N http://localhost:8000/api/v1/runs/run-abc123/stream

# Server-Sent Events output:
data: {"variation_id": 0, "content": "Analyzing repository structure...", "timestamp": "..."}
data: {"variation_id": 1, "content": "Starting code review...", "timestamp": "..."}
```

### Select Winner

```bash
curl -X POST http://localhost:8000/api/v1/runs/run-abc123/select \
  -H "Content-Type: application/json" \
  -d '{"variation_id": 1}'
```

## 🎨 Design System

AIdeator uses a custom design system optimized for multi-agent interfaces:

### Colors
- **AI Primary** (`#4f46e5`): Main actions and branding
- **Agent Colors**: Red, Amber, Emerald, Blue, Purple (for 5 agents)
- **Neutral Palette**: White, Paper, Fog, Shadow, Charcoal

### Components
- **Agent Stream Cards**: Color-coded with status indicators
- **Responsive Grid**: 1-5 columns based on screen size
- **Real-time Animations**: Pulse indicators and shimmer loading

### Typography
- **Display** (48px): Hero titles
- **H1-H3**: Page and section headers
- **Body**: 16px default with Large (18px) and Small (14px) variants

## 🚀 Deployment

### Development (Local)
```bash
# Already covered above with Tilt
tilt up
```

### Staging
```bash
# Deploy to staging cluster
helm upgrade --install aideator ./deploy/charts/aideator \
  -n aideator-staging \
  -f deploy/values/staging.yaml
```

### Production
```bash
# Deploy to production cluster
helm upgrade --install aideator ./deploy/charts/aideator \
  -n aideator-prod \
  -f deploy/values/production.yaml \
  --atomic \
  --wait
```

## 🐛 Troubleshooting

### Common Issues

**Frontend not connecting to backend:**
```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check Tilt status
tilt get uiresource
```

**Kubernetes Jobs failing:**
```bash
# Check job status
kubectl get jobs -n aideator

# Debug specific job
kubectl describe job agent-run123-0 -n aideator
kubectl logs job/agent-run123-0 -n aideator
```

**Streaming not working:**
```bash
# Test SSE endpoint directly
curl -N http://localhost:8000/api/v1/runs/test-run/stream

# Check for CORS issues in browser console
```

**Tilt build failures:**
```bash
# Clean rebuild
tilt down
docker system prune -f
tilt up
```

### Required Secrets

Before deployment, create required Kubernetes secrets:

```bash
# OpenAI API key (required for agents)
kubectl create secret generic openai-secret \
  --from-literal=api-key="$OPENAI_API_KEY" \
  -n aideator

# Application secret key
kubectl create secret generic aideator-secret \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  -n aideator
```

## 📊 Monitoring

- **Tilt UI**: http://localhost:10350 (development)
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Kubernetes Dashboard**: Access via kubectl proxy

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test locally with Tilt
4. Run linting and tests
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Development Guidelines

- **Backend**: Follow FastAPI patterns, use async/await, comprehensive type hints
- **Frontend**: Use TypeScript, follow component patterns, responsive design
- **Testing**: Write tests for new features, test with real Kubernetes
- **Documentation**: Update README and API docs for changes

## 📋 Project Status

**Current Version**: 3.0 - Full-Stack Implementation

**Completed Features** ✅
- [x] Kubernetes-native backend with FastAPI
- [x] Next.js frontend with custom design system
- [x] Real-time streaming via Server-Sent Events
- [x] Multi-agent orchestration (1-5 agents)
- [x] Responsive UI with agent comparison
- [x] Tilt development environment
- [x] Helm chart deployment

**Next Steps** 🚧
- [ ] End-to-end Playwright testing
- [ ] Performance optimization
- [ ] Mobile UX enhancements
- [ ] Monitoring and observability
- [ ] Production hardening

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Next.js](https://nextjs.org/)
- Kubernetes development with [Tilt](https://tilt.dev/)
- UI components inspired by [shadcn/ui](https://ui.shadcn.com/)

---

**Made with ❤️ for developers who want to harness the power of multi-agent AI**