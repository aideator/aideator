# Phase 2: Redis as Primary Streaming Backend

## Overview

Phase 2 makes Redis the primary streaming mechanism while maintaining kubectl logs as a fallback. This provides improved reliability, better reconnection handling, and sets the foundation for Phase 3 (Redis-only).

## Implementation Summary

### 1. Frontend Configuration

**Environment Variables** (`.env.local`):
```bash
NEXT_PUBLIC_STREAMING_BACKEND=redis  # Use Redis SSE endpoint
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 2. Frontend Updates

**Dynamic Endpoint Selection** (`useAgentStream.ts`):
- Automatically chooses `/stream/redis` or `/stream` based on config
- Enhanced reconnection logic with exponential backoff
- Redis gets more retry attempts (10) vs kubectl (3)
- Visual indicator shows which backend is active

**API Client Updates**:
- Uses `NEXT_PUBLIC_API_BASE_URL` environment variable
- Consistent configuration across all API calls

### 3. Backend Enhancements

**Redis SSE Endpoint** (`/api/v1/runs/{run_id}/stream/redis`):
- Heartbeat every 30 seconds to keep connection alive
- Proper async task management with cleanup
- Converts Redis pub/sub messages to SSE events
- Same event format as kubectl endpoint for compatibility

### 4. Testing

**Test Script** (`scripts/test_redis_streaming.py`):
```bash
python scripts/test_redis_streaming.py
```

**Manual Testing**:
```bash
# Monitor Redis activity
redis-cli psubscribe "run:*"

# Test SSE endpoints
curl -N http://localhost:8000/api/v1/runs/{run_id}/stream/redis
```

## How It Works

1. **Agent publishes to both stdout and Redis** (dual publishing)
2. **Frontend connects to Redis SSE endpoint** by default
3. **Redis SSE subscribes to all run channels**:
   - `run:{run_id}:output:*` - Agent outputs
   - `run:{run_id}:status` - Status updates
   - `run:{run_id}:logs:*` - System logs (filtered)
4. **Heartbeats maintain connection** every 30 seconds
5. **Automatic reconnection** with exponential backoff

## Advantages Over kubectl Streaming

1. **Reliability**: No subprocess pipes to break
2. **Performance**: Direct pub/sub vs parsing logs
3. **Flexibility**: Can subscribe to specific channels
4. **Observability**: `redis-cli monitor` for debugging
5. **Scalability**: Redis handles many subscribers efficiently

## Switching Between Backends

To use kubectl streaming (fallback):
```bash
# In frontend/.env.local
NEXT_PUBLIC_STREAMING_BACKEND=kubectl
```

To use Redis streaming (default):
```bash
# In frontend/.env.local
NEXT_PUBLIC_STREAMING_BACKEND=redis
```

## Next Steps (Phase 3)

1. Remove kubectl log streaming code
2. Implement Redis Streams for persistence
3. Add replay capability for reconnections
4. Remove dual publishing from agent
5. Simplify orchestrator

## Monitoring

Check streaming backend:
- Look for badge in UI: "Redis Streaming" or "Kubectl Streaming"
- Check browser console for connection logs
- Monitor Redis: `redis-cli monitor`
- API health: `curl http://localhost:8000/health`

The system now runs primarily on Redis while maintaining full backward compatibility. Ready for production testing, it is.