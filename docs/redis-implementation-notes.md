# Redis Implementation Notes

## Overview

Redis has been added to the AIdeator development environment as a foundational component for replacing the fragile kubectl logs streaming pipeline. This document details the current implementation, security considerations, and usage patterns.

## Current Implementation Status

### What's Implemented
1. **Redis Deployment** - Redis 7 Alpine running in Kubernetes
2. **Service Discovery** - Available at `aideator-redis:6379` within cluster
3. **Port Forwarding** - Local access via `localhost:6379`
4. **Environment Variables** - `REDIS_URL` configured for API and agents
5. **Python Dependency** - `redis>=5.0.0` in requirements.txt

### What's NOT Implemented Yet
1. **No Pub/Sub code** - Redis is deployed but not used for streaming
2. **No data persistence** - Redis restarts lose all data
3. **No authentication** - Security traded for development ease
4. **No clustering/HA** - Single Redis instance only

## Architecture Details

### Kubernetes Resources

```yaml
# Deployment: aideator-redis
- Image: redis:7-alpine
- Replicas: 1
- Resources: 128Mi-512Mi memory, 100m-500m CPU
- Command: redis-server --save "" --appendonly no

# Service: aideator-redis
- Type: ClusterIP
- Port: 6379
- Selector: app=redis
```

### Network Topology

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Agent Pods    │────▶│  Redis Service  │◀────│    API Pod      │
│ REDIS_URL env   │     │ aideator-redis  │     │ REDIS_URL env   │
└─────────────────┘     │    :6379        │     └─────────────────┘
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   Redis Pod     │
                        │ No persistence  │
                        └─────────────────┘
```

### Environment Configuration

**API Deployment:**
```bash
REDIS_URL=redis://aideator-redis:6379/0
```

**Agent Jobs:**
```bash
REDIS_URL=redis://aideator-redis:6379/0
```

## Security Considerations

### Development Tradeoffs Made

1. **No Authentication**
   - Risk: Any pod in cluster can access Redis
   - Justification: Simplifies development, no secret management
   - Production fix: Enable Redis AUTH with password

2. **No Encryption**
   - Risk: Data transmitted in plain text
   - Justification: Local cluster, no sensitive data in dev
   - Production fix: TLS encryption with Redis 6+

3. **Open Port Forwarding**
   - Risk: Anyone on localhost can connect to Redis
   - Justification: Enables easy debugging with redis-cli
   - Production fix: Remove port forwarding, use kubectl exec

4. **No ACLs**
   - Risk: Full access to all keys from any client
   - Justification: Simple development without permission complexity
   - Production fix: Redis ACLs per service/user

5. **No Persistence**
   - Risk: Data loss on pod restart
   - Justification: Faster performance, clean state each run
   - Production fix: Enable AOF or RDB persistence

## Usage Patterns

### Basic Connection Testing

```bash
# From local machine (after tilt up)
redis-cli ping
# PONG

# Set and get values
redis-cli set test "hello world"
redis-cli get test
# "hello world"

# Monitor all commands in real-time
redis-cli monitor
```

### Python Connection Examples

```python
# Basic connection
import redis
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Test connection
r.ping()  # True

# Key-value operations
r.set("key", "value")
r.get("key")  # b'value'

# Pub/Sub (future streaming)
pubsub = r.pubsub()
pubsub.subscribe("channel:test")
for message in pubsub.listen():
    print(message)
```

### Proposed Channel Structure

```
# Agent output streaming
run:{run_id}:output:{variation_id}    # LLM responses
run:{run_id}:logs:{variation_id}      # System logs
run:{run_id}:status                   # Job status updates

# Control channels
run:{run_id}:control                  # Commands to agents
agent:{agent_id}:heartbeat            # Agent health

# Metrics
metrics:api:requests                  # API metrics
metrics:agent:tokens                  # Token usage
```

## Development Workflow

### Starting Redis
```bash
# Redis starts automatically with Tilt
tilt up

# Verify Redis is running
kubectl get pods -n aideator | grep redis
# aideator-redis-xxxxx    1/1     Running
```

### Debugging Redis

```bash
# View Redis logs
kubectl logs -n aideator -l app=redis

# Execute Redis commands in pod
kubectl exec -it -n aideator deployment/aideator-redis -- redis-cli

# Local debugging
redis-cli -h localhost -p 6379
```

### Common Operations

```bash
# Flush all data
redis-cli flushall

# Check memory usage
redis-cli info memory

# List all keys (dev only!)
redis-cli keys '*'

# Monitor pub/sub channels
redis-cli psubscribe 'run:*'
```

## Integration Points

### Current Code Preparation

**app/core/config.py:**
```python
redis_url: Optional[str] = Field(None, description="Redis connection URL")
redis_password: Optional[str] = Field(None, description="Redis password")
redis_db: int = Field(0, description="Redis database number")
```

### Future Integration Example

```python
# app/services/redis_streaming.py (not implemented yet)
class RedisStreamingService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
    
    async def publish_agent_output(self, run_id: str, variation_id: str, content: str):
        channel = f"run:{run_id}:output:{variation_id}"
        await self.redis.publish(channel, content)
    
    async def subscribe_to_run(self, run_id: str):
        pattern = f"run:{run_id}:*"
        await self.pubsub.psubscribe(pattern)
        async for message in self.pubsub.listen():
            yield message
```

## Performance Considerations

### Current Settings
- No persistence = Maximum performance
- No eviction policy = Will OOM if overloaded
- Single instance = No replication overhead
- Alpine image = Minimal memory footprint

### Capacity Planning
- ~1MB per 1000 messages (average)
- 512MB limit = ~500k messages
- Pub/Sub has no persistence by default
- Consider Redis Streams for durability

## Migration Path

### Phase 1: Parallel Operation (Current)
- ✅ Redis deployed and accessible
- ⏳ Add Redis publishing alongside stdout
- ⏳ Keep kubectl logs as primary

### Phase 2: Redis Primary
- Switch SSE to use Redis subscriptions
- kubectl logs as fallback only
- Add message persistence

### Phase 3: Redis Only
- Remove kubectl streaming code
- Implement full pub/sub patterns
- Add production hardening

## Troubleshooting

### Redis Won't Start
```bash
# Check pod status
kubectl describe pod -n aideator -l app=redis

# Common issues:
# - Resource limits too low
# - Node out of resources
# - Image pull issues
```

### Connection Refused
```bash
# Verify service exists
kubectl get svc -n aideator aideator-redis

# Check Redis is listening
kubectl exec -n aideator deployment/aideator-redis -- netstat -tlnp
```

### Memory Issues
```bash
# Check Redis memory
kubectl exec -n aideator deployment/aideator-redis -- redis-cli info memory

# Emergency flush
kubectl exec -n aideator deployment/aideator-redis -- redis-cli flushall
```

## Security Hardening Checklist (For Production)

- [ ] Enable Redis AUTH password
- [ ] Configure Redis ACLs per service
- [ ] Enable TLS encryption
- [ ] Remove port forwarding
- [ ] Add network policies
- [ ] Enable persistence (AOF/RDB)
- [ ] Set up Redis Sentinel for HA
- [ ] Configure memory eviction policy
- [ ] Add monitoring/alerting
- [ ] Implement connection pooling
- [ ] Add rate limiting

## Next Steps

1. **Implement Redis Publisher in Agent**
   - Replace stdout with Redis publish
   - Use structured message format
   - Add error handling

2. **Create SSE Redis Subscriber**
   - Subscribe to run channels
   - Convert to SSE events
   - Handle reconnections

3. **Add Integration Tests**
   - Test pub/sub reliability
   - Verify message ordering
   - Load test throughput

4. **Performance Optimization**
   - Connection pooling
   - Batch publishing
   - Message compression

The foundation is laid. Redis awaits its purpose, ready it is.