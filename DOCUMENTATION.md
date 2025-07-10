# AIdeator Documentation

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Redis Streaming Migration](#redis-streaming-migration)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

## Overview

AIdeator is a Kubernetes-native multi-agent AI orchestration platform that runs multiple AI agents in parallel in isolated containers, streaming their thought processes in real-time via Server-Sent Events (SSE).

### Key Features
- **Parallel Agent Execution**: Run 1-5 AI agent variations simultaneously
- **Container Isolation**: Each agent runs in its own Kubernetes Job
- **Real-time Streaming**: Live output via SSE with Redis pub/sub or kubectl logs
- **Model Flexibility**: Support for LiteLLM (OpenAI, Anthropic, etc.) and Claude Code CLI
- **GitHub Integration**: Analyze any public repository
- **Result Persistence**: Select and save winning variations

## Architecture

### System Components
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│ Kubernetes  │
│  (Next.js)  │◀────│   Backend   │◀────│    Jobs     │
└─────────────┘ SSE └─────────────┘     └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    Redis    │
                     │  (Pub/Sub)  │
                     └─────────────┘
```

### Data Flow
1. User submits run request via frontend
2. Backend creates Kubernetes Jobs for each agent variation
3. Agents stream output via stdout and Redis pub/sub
4. Backend aggregates streams and sends to frontend via SSE
5. Frontend displays real-time output in grid layout

## Redis Streaming Migration

### Overview
AIdeator has migrated from kubectl logs-based streaming to Redis pub/sub as the primary streaming mechanism. This provides improved reliability, better performance, and enables future enhancements.

### Migration Phases

#### Phase 1: Dual Publishing (Completed)
- Agents publish to both stdout (for kubectl logs) and Redis
- Both streaming endpoints available
- Zero disruption to existing functionality

#### Phase 2: Redis Primary (Current)
- Redis is now the default streaming backend
- kubectl logs remains as fallback option
- Frontend can switch between backends via UI toggle

#### Phase 3: Redis Only (Planned)
- Remove kubectl streaming code entirely
- Implement Redis Streams for persistence
- Add replay capability for reconnections

### Redis Architecture

#### Channel Structure
```
run:{run_id}:output:{variation_id}  # Agent LLM outputs
run:{run_id}:logs:{variation_id}    # System logs (filtered)
run:{run_id}:status                 # Job status updates
run:{run_id}:control                # Future: control messages
```

#### Message Format
```json
{
  "content": "Agent output text",
  "timestamp": "2024-01-10T10:30:00Z",
  "variation_id": "0"
}
```

### Configuration

#### Backend Configuration
```bash
# .env file
REDIS_URL=redis://localhost:6379/0
```

#### Frontend Configuration
```bash
# frontend/.env.local
NEXT_PUBLIC_STREAMING_BACKEND=redis  # or 'kubectl' for fallback
```

#### Runtime Configuration
Users can switch streaming backends via the "Advanced Settings" panel in the run creation form:
- **Redis Pub/Sub** (default) - Better reliability and performance
- **Kubectl Logs** - Legacy fallback option

### Benefits of Redis Streaming

1. **Reliability**
   - No subprocess pipes to break
   - Automatic reconnection handling
   - Built-in buffering

2. **Performance**
   - Direct pub/sub vs log parsing
   - Lower latency
   - Better scalability

3. **Features**
   - Bidirectional communication (future)
   - Message persistence with Redis Streams (future)
   - Pattern subscriptions for monitoring

4. **Observability**
   - `redis-cli monitor` for debugging
   - Pub/sub metrics
   - Channel introspection

### Monitoring Redis Streaming

#### Check Redis Connection
```bash
# API health endpoint shows Redis status
curl http://localhost:8000/health

# Direct Redis connection test
redis-cli ping
```

#### Monitor Active Streams
```bash
# Watch all messages for a run
redis-cli psubscribe "run:*"

# Monitor specific run
redis-cli psubscribe "run:${RUN_ID}:*"

# Count subscribers
redis-cli pubsub numsub "run:${RUN_ID}:output:0"
```

#### Debug Streaming Issues
```bash
# Test Redis streaming endpoint
curl -N http://localhost:8000/api/v1/runs/${RUN_ID}/stream/redis

# Compare with kubectl endpoint
curl -N http://localhost:8000/api/v1/runs/${RUN_ID}/stream

# Check Redis memory usage
redis-cli info memory
```

### Troubleshooting

#### Redis Connection Failed
- Verify Redis is running: `kubectl get pods -n aideator | grep redis`
- Check Redis service: `kubectl get svc -n aideator aideator-redis`
- Test connection: `redis-cli -h localhost -p 6379 ping`

#### No Stream Output
- Verify agent is publishing: `redis-cli monitor`
- Check correct channel: `redis-cli pubsub channels`
- Verify run exists: Check API `/runs/{run_id}/status`

#### Stream Disconnections
- Check browser console for reconnection attempts
- Verify heartbeat messages arriving (every 30s)
- Check Redis memory: `redis-cli info memory`

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
- `REDIS_URL` - Redis connection string (default: `redis://localhost:6379/0`)
- `DATABASE_URL` - Database connection (default: SQLite)
- `SECRET_KEY` - API secret key
- `MAX_VARIATIONS` - Maximum agent variations (default: 5)

### Frontend Configuration
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_STREAMING_BACKEND` - Default streaming backend (`redis` or `kubectl`)
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

#### Test Redis Streaming
```python
# Run test script
python scripts/test_redis_streaming.py
```

#### Test Agent Locally
```bash
# Set environment variables
export REDIS_URL=redis://localhost:6379
export RUN_ID=test-123
export VARIATION_ID=0

# Run agent
python agent/main.py
```

#### Test SSE Endpoints
```bash
# Redis endpoint
curl -N http://localhost:8000/api/v1/runs/${RUN_ID}/stream/redis

# kubectl endpoint (fallback)
curl -N http://localhost:8000/api/v1/runs/${RUN_ID}/stream
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

### Load Testing Redis Streaming
```bash
# Create multiple subscribers
for i in {1..10}; do
  curl -N http://localhost:8000/api/v1/runs/load-test/stream/redis &
done

# Publish test messages
redis-cli publish "run:load-test:output:0" '{"content":"Test message"}'
```

## Deployment

### Production Considerations

#### Redis Configuration
- Use Redis Sentinel or Cluster for HA
- Enable persistence (AOF or RDB)
- Set appropriate memory limits
- Configure eviction policies

#### Security
- Enable Redis AUTH
- Use TLS for Redis connections
- Implement network policies
- Set resource quotas

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

#### Create Run
```
POST /api/v1/runs
{
  "github_url": "https://github.com/user/repo",
  "prompt": "Analyze this repository",
  "variations": 3,
  "use_claude_code": false,
  "agent_config": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

#### Stream Output (Redis)
```
GET /api/v1/runs/{run_id}/stream/redis
```
Server-Sent Events with:
- `agent_output` - Agent responses
- `agent_complete` - Variation finished
- `run_complete` - All agents done
- `heartbeat` - Keep-alive signal

#### Select Winner
```
POST /api/v1/runs/{run_id}/select
{
  "variation_id": 0
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.