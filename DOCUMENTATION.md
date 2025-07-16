# AIdeator Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Reference](#api-reference)

## Overview

AIdeator is a Kubernetes-native multi-agent AI orchestration platform that runs multiple AI agents in parallel in isolated containers, with real-time progress monitoring through HTTP polling.

### Key Features
- **Parallel Agent Execution**: Run 1-6 AI agent variations simultaneously
- **Container Isolation**: Each agent runs in its own Kubernetes Job
- **Real-time Monitoring**: Live output via HTTP polling of PostgreSQL
- **Model Flexibility**: Support for Claude CLI, Gemini CLI, and other providers
- **GitHub Integration**: Analyze any public repository
- **Unified Task System**: Simplified task/run architecture with embedded JSON

## Architecture

### System Components
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│ Kubernetes  │
│  (Next.js)  │◀────│   Backend   │     │    Jobs     │
└─────────────┘HTTP └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                     ┌─────────────┐      ┌──────────┐
                     │ PostgreSQL  │◀─────│  Agent   │
                     │   Database  │      │Container │
                     └─────────────┘      └──────────┘
```

### Data Flow
1. User submits task request via frontend
2. Backend creates Kubernetes Jobs for each agent variation
3. Agents write outputs directly to PostgreSQL `task_outputs` table
4. Frontend polls `/api/v1/tasks/{task_id}/outputs` every 3 seconds
5. Frontend displays real-time output in tabbed interface

### Database Architecture

#### Unified Task System
The system uses a simplified PostgreSQL-based architecture:

```sql
-- Primary tables
tasks          -- Main task metadata and configuration
task_outputs   -- All agent outputs with timestamps
users          -- User management (optional in dev mode)
```

#### Output Types
Agent outputs are categorized by type in the `task_outputs` table:
- `job_data` - Main job execution data
- `assistant_response` - AI model responses
- `error` - Error messages
- `system_status` - System-level status updates
- `debug` - Debug information (when enabled)
- `stdout`/`stderr` - Raw command outputs
- `diffs` - Code differences
- `summary` - Task summaries

### Polling Architecture

The system uses HTTP polling for real-time updates:

1. **Frontend Hook** (`use-agent-logs.ts`):
   - Polls every 3 seconds
   - Implements 5-second cache to reduce API load
   - Fetches from `/api/v1/tasks/{taskId}/outputs`

2. **API Endpoint**:
   - Supports filtering by `since` timestamp
   - Can filter by `variation_id` and `output_type`
   - Returns up to 1000 outputs per request

3. **Performance Optimizations**:
   - Client-side caching reduces redundant requests
   - Timestamp-based filtering minimizes data transfer
   - Indexed database queries for fast retrieval

## Getting Started

### Prerequisites
- Docker Desktop with Kubernetes enabled
- Python 3.11+
- Node.js 18+
- kubectl
- Tilt

### Quick Start
```bash
# Clone repository
git clone https://github.com/aideator/aideator.git
cd aideator

# Run bootstrap script
./bootstrap.sh

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start development environment
tilt up

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Redis: localhost:6379
```

## Configuration

### Environment Variables

#### Required
- `OPENAI_API_KEY` - For LiteLLM models
- `ANTHROPIC_API_KEY` - For Claude Code CLI

#### Optional
- `DATABASE_URL` - PostgreSQL connection (default: `postgresql://aideator:aideator123@localhost:5432/aideator`)
- `SECRET_KEY` - API secret key
- `MAX_VARIATIONS` - Maximum agent variations (default: 3)
- `GEMINI_API_KEY` - For Gemini CLI agent mode
- `SIMPLE_DEV_MODE` - Enable development mode with auth bypass (default: true)

### Frontend Configuration
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)
- `PORT` - Frontend port (default: 3000)

## Development

### Local Development with Tilt
```bash
# Start all services
tilt up

# View Tilt UI
open http://localhost:10350

# Stop services
tilt down
```

### Testing Components Individually

#### Test Agent Locally
```bash
# Set environment variables
export DATABASE_URL=postgresql://aideator:aideator123@localhost:5432/aideator
export TASK_ID=1
export VARIATION_ID=0
export REPO_URL=https://github.com/octocat/Hello-World
export PROMPT="Analyze this repository"
export AGENT_MODE=claude-cli

# Run agent
python agent/main.py
```

#### Test API Endpoints
```bash
# Create a new task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "prompt": "Analyze this repository",
    "model_names": ["gpt-4o-mini"],
    "agent_mode": "claude-cli"
  }'

# Poll for outputs
curl http://localhost:8000/api/v1/tasks/{task_id}/outputs
```

## Testing

### Unit Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test
```

### E2E Tests
```bash
cd frontend && npm run test:e2e
```

### Load Testing
```bash
# Create multiple concurrent tasks
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d '{"github_url": "https://github.com/octocat/Hello-World", "prompt": "Test task '$i'"}' &
done

# Monitor database load
watch -n 1 'psql -U aideator -d aideator -c "SELECT COUNT(*) FROM task_outputs"'
```

## Deployment

### Production Considerations

#### Database Configuration
- Use PostgreSQL with replication for HA
- Configure connection pooling
- Set appropriate memory and CPU limits
- Regular backups and point-in-time recovery

#### Security
- Use strong database passwords
- Enable SSL/TLS for database connections
- Implement network policies
- Set resource quotas
- Store API keys in Kubernetes secrets

#### Scaling
- Horizontal pod autoscaling for API
- Redis Cluster for high throughput
- Consider CDN for frontend
- Database connection pooling

### Kubernetes Deployment
```bash
# Create namespace
kubectl create namespace aideator

# Create secrets
kubectl create secret generic openai-secret \
  --from-literal=api-key="$OPENAI_API_KEY" \
  -n aideator

# Deploy with Helm
helm install aideator ./deploy/charts/aideator \
  --namespace aideator \
  --values ./deploy/values/production.yaml
```

## API Reference

### Key Endpoints

#### Create Task
```
POST /api/v1/tasks
{
  "github_url": "https://github.com/user/repo",
  "prompt": "Analyze this repository",
  "model_names": ["gpt-4o-mini", "claude-3-5-sonnet"],
  "agent_mode": "claude-cli",
  "variations": 2  // Optional, defaults to len(model_names)
}

Response:
{
  "task_id": 123,
  "websocket_url": "/ws/tasks/123",  // Not implemented
  "polling_url": "/api/v1/tasks/123/outputs",
  "status": "pending"
}
```

#### List Tasks
```
GET /api/v1/tasks?limit=10&offset=0

Response:
{
  "tasks": [
    {
      "id": "123",
      "title": "Analyze this repository",
      "details": "10:30 AM · aideator/repo",
      "status": "Completed",
      "versions": 2,
      "additions": 150,
      "deletions": 30
    }
  ],
  "total": 50,
  "has_more": true
}
```

#### Get Task Details
```
GET /api/v1/tasks/{task_id}
```
Returns task metadata with variation details.

#### Get Task Outputs (Polling)
```
GET /api/v1/tasks/{task_id}/outputs?since=2024-01-01T00:00:00Z&variation_id=0&output_type=assistant_response

Query params:
- since: ISO timestamp to get outputs after
- variation_id: Filter by specific variation (0, 1, 2...)
- output_type: Filter by type (job_data, error, assistant_response, etc.)
- limit: Max outputs to return (default 100, max 1000)

Response:
[
  {
    "id": 1,
    "task_id": 123,
    "variation_id": 0,
    "content": "Agent output text",
    "timestamp": "2024-01-01T10:30:00Z",
    "output_type": "assistant_response"
  }
]
```

#### Get Variation Outputs
```
GET /api/v1/tasks/{task_id}/variations/{variation_id}/outputs
```
Same as above but pre-filtered to a specific variation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.