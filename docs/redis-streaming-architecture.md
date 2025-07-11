# Redis Pub/Sub Streaming Architecture Plan

## Executive Summary

Replace the fragile kubectl logs streaming pipeline with Redis Pub/Sub for improved reliability, simplified architecture, and enhanced functionality. This plan outlines a phased migration from the current system to a Redis-based streaming solution.

## Current Architecture Problems

### Fragility Points
- **kubectl logs process**: Single point of failure, no automatic recovery
- **Subprocess pipes**: Can break silently, difficult to debug
- **No persistence**: Any failure loses in-flight messages
- **No backpressure**: Queue overflow = silent data loss
- **Complex filtering**: Manual JSON parsing and routing logic
- **Race conditions**: Job creation vs log streaming timing issues

### Operational Issues
- Pod crashes result in permanent stream loss
- No bidirectional communication capability
- Limited observability into streaming pipeline
- Resource leaks in long-running streams
- No replay capability for missed messages

## Proposed Redis Architecture

### Core Design
```
Agent Container → Redis Client → Redis Pub/Sub → SSE Endpoints → Frontend
```

### Channel Structure
```
run:{run_id}:output:{variation_id}    # LLM output (markdown/text)
run:{run_id}:logs:{variation_id}      # System logs (JSON)
run:{run_id}:status                   # Job status updates
run:{run_id}:control                  # Control messages to agents
run:{run_id}:metrics                  # Performance metrics
```

### Key Improvements

#### 1. Decoupled Components
- Agents publish directly to Redis (no stdout parsing)
- SSE endpoints subscribe to Redis channels
- Components can fail/restart independently
- No subprocess management or pipe handling

#### 2. Built-in Reliability
- Redis handles all reconnection logic
- Automatic buffering and retry
- Optional Redis Streams for persistence
- Redis Sentinel/Cluster for HA

#### 3. Enhanced Features
- Bidirectional communication (pause/resume/stop agents)
- Real-time metrics and monitoring
- Message replay capability
- Pattern subscriptions for global monitoring
- TTL-based automatic cleanup

#### 4. Operational Benefits
- Redis MONITOR for debugging
- Built-in pub/sub metrics
- No kubectl dependency
- Simplified error handling

## Implementation Phases

### Phase 1: Parallel Operation (2-3 weeks)
**Goal**: Add Redis alongside existing system for risk-free testing

#### Agent Changes
- Add Redis client to agent container
- Publish to both stdout AND Redis
- Maintain backward compatibility
- Add Redis connection error handling

#### Backend Changes
- Deploy Redis in Kubernetes cluster
- Create new SSE endpoint using Redis subscriptions
- Keep existing kubectl-based endpoint
- Add Redis health checks

#### Frontend Changes
- Add feature flag for Redis vs kubectl streaming
- No other changes needed (same SSE events)

#### Testing
- A/B test both streaming methods
- Compare reliability metrics
- Monitor Redis performance
- Verify message ordering

### Phase 2: Redis Primary (2 weeks)
**Goal**: Make Redis the primary streaming mechanism

#### Changes
- Default all new runs to Redis streaming
- kubectl logs becomes debugging fallback only
- Add Redis Streams for persistence
- Implement message replay on reconnect

#### Monitoring
- Alert on Redis connection failures
- Track message delivery metrics
- Monitor memory usage
- Set up Redis persistence

### Phase 3: Full Migration (1 week)
**Goal**: Remove kubectl streaming entirely

#### Cleanup
- Remove KubernetesService log streaming code
- Simplify AgentOrchestrator
- Remove kubectl dependency
- Update documentation

#### Enhancements
- Add bidirectional control messages
- Implement agent acknowledgments
- Add real-time configuration updates
- Enable cross-agent communication

## Technical Design Details

### Redis Deployment
```yaml
Mode: Redis Sentinel (3 nodes)
Persistence: AOF with fsync every second
Memory: 2GB per node
Eviction: allkeys-lru
Connection pooling: 100 connections
```

### Message Format
```json
{
  "timestamp": "2024-01-10T10:30:00Z",
  "run_id": "run-abc123",
  "variation_id": "var-1",
  "sequence": 1234,
  "type": "output|log|status|metric",
  "content": "...",
  "metadata": {}
}
```

### Security Model
- Redis ACLs per run_id
- TLS for all connections
- Separate users for agents vs SSE
- Channel pattern restrictions
- Connection rate limiting

### Error Handling
- Exponential backoff on connection failure
- Circuit breaker for Redis outages
- Fallback to in-memory queuing
- Dead letter queue for failed messages
- Automatic reconnection with replay

## Migration Risks & Mitigations

### Risks
1. **New Infrastructure Dependency**
   - Mitigation: Redis is mature, well-understood
   - Fallback: Can quickly revert to kubectl

2. **Message Ordering**
   - Mitigation: Add sequence numbers
   - Use Redis Streams for ordering guarantees

3. **Memory Usage**
   - Mitigation: TTL on all keys
   - Monitor and alert on memory

4. **Network Partitions**
   - Mitigation: Redis Sentinel for HA
   - Client-side buffering

## Success Metrics

### Reliability
- 99.9% message delivery rate
- <100ms end-to-end latency
- Zero message loss during failovers
- Automatic recovery from all failure modes

### Operational
- 50% reduction in streaming-related code
- 90% reduction in streaming-related bugs
- Simplified debugging and monitoring
- Eliminated kubectl dependency

### Performance
- 10x increase in supported concurrent streams
- Linear scalability with Redis Cluster
- Consistent performance under load
- Reduced CPU usage on backend

## Future Enhancements

### Short Term (Q2)
- Redis Streams for guaranteed delivery
- Message compression for large outputs
- Batch publishing for efficiency
- WebSocket upgrade option

### Medium Term (Q3)
- Cross-region replication
- Advanced routing rules
- Message transformation pipeline
- Analytics on streaming data

### Long Term (Q4+)
- Event sourcing architecture
- CQRS pattern implementation
- GraphQL subscriptions
- Full event-driven architecture

## Conclusion

This Redis-based architecture dramatically simplifies the streaming pipeline while adding reliability, scalability, and new capabilities. The phased approach ensures zero downtime and easy rollback if needed. The end result is a production-ready streaming system that can scale with the platform's growth.

Key benefits:
- **Simplicity**: 50% less code, easier to understand
- **Reliability**: Built-in failure recovery, message persistence
- **Scalability**: Redis Cluster for horizontal scaling
- **Features**: Bidirectional communication, replay, metrics
- **Operations**: Better monitoring, debugging, and control

This is the way forward for a robust, scalable streaming architecture.