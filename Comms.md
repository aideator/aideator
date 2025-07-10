 Technical Analysis: Frontend Job Execution and Streaming Architecture

  Job Kickoff Flow

  1. Frontend initiates via RunForm component → POST to /api/v1/runs
  2. Backend creates Kubernetes Jobs asynchronously using job templates
  3. Each variation runs as isolated container executing agent/main.py
  4. Immediate SSE connection established for real-time streaming

  Communication Pipeline

  Agent → Frontend Data Flow:
  Agent (stdout) → kubectl logs -f → KubernetesService → AgentOrchestrator
  (filter) → SSEManager → Frontend EventSource

  Output Formats:
  - System logs: JSON with timestamp/level (filtered out)
  - LLM output: Plain text with 🔸 prefix (passed through)
  - All output uses stdout with flush=True for real-time streaming

  Critical Technical Details

  Streaming Characteristics:
  - Uses kubectl logs -f for real-time following
  - No buffering at transport layers
  - SSE events wrapped with variation_id and timestamp
  - Frontend StreamBuffer respects word/markdown boundaries

  Filtering Logic:
  if 'timestamp' in log_entry and 'level' in log_entry:
      # System log - filter out
  else:
      # LLM output - send to frontend

  Major Edge Cases & Concerns

  1. Reliability Issues:
    - No kubectl reconnection on failure
    - Silent data loss on SSE queue overflow
    - No message persistence or delivery guarantees
  2. Resource Risks:
    - Unbounded frontend memory growth
    - No streaming backpressure mechanism
    - Missing activeDeadlineSeconds on jobs
  3. Race Conditions:
    - Job creation vs log streaming start
    - Client connection before job exists
    - Out-of-order delivery with multiple pods
  4. Security Vulnerabilities:
    - No output sanitization (SSE injection risk)
    - Prompt passed via environment variable
    - Potential secret exposure in logs
  5. Operational Gaps:
    - Pod crashes = permanent stream loss
    - No metrics or distributed tracing
    - TTL mismatch with agent sleep duration

  The architecture achieves real-time multi-agent streaming but needs
  significant hardening for production reliability and security. Fragile in
  production, this pipeline would be.

> i'd like to simplify this (with same or more functionality with more
  reliability).  don't code.  just discuss.  what about using a redis server
  doing pub/sub with SSE realtime.

⏺ Architectural Simplification with Redis Pub/Sub

  Current Architecture Pain Points

  The current pipeline is fragile because it chains together multiple stateful
  processes:
  - kubectl logs -f → subprocess pipe → Python async reading → filtering → SSE
  broadcasting
  - Each link can fail independently with no recovery mechanism
  - No persistence means any failure loses data

  Redis Pub/Sub Architecture

  Simplified Flow:
  Agent → Redis PUBLISH → Redis Pub/Sub → SSE Subscribers

  Key Improvements

  1. Decoupled Components
    - Agent publishes directly to Redis channels
  (run:{run_id}:variation:{var_id})
    - No kubectl logs dependency - agent uses Redis client
    - SSE endpoints simply subscribe to Redis channels
    - Components can fail/restart independently
  2. Built-in Reliability
    - Redis handles reconnections automatically
    - Pub/Sub has built-in buffering
    - Can add Redis Streams for persistence/replay
    - Redis Sentinel for HA if needed
  3. Cleaner Streaming
    - No parsing kubectl output
    - No subprocess management
    - No manual filtering - use different channels
    - Native JSON support in Redis

  Implementation Patterns

  Channel Structure:
  run:{run_id}:output:{variation_id}  # LLM output
  run:{run_id}:logs:{variation_id}    # System logs
  run:{run_id}:status                 # Job status updates
  run:{run_id}:control                # Commands to agents

  Agent Side:
  # Instead of print(json.dumps(log_entry))
  redis_client.publish(f"run:{run_id}:logs:{variation_id}", log_entry)

  # Instead of print(f"🔸 {line}")
  redis_client.publish(f"run:{run_id}:output:{variation_id}", line)

  Additional Benefits

  1. Bidirectional Communication
    - Frontend could send control messages (pause/resume/stop)
    - Agents could acknowledge receipt
    - Real-time parameter adjustments
  2. Better Observability
    - Redis MONITOR for debugging
    - Built-in pub/sub metrics
    - Can tap into any channel for debugging
  3. Scalability
    - Redis Cluster for horizontal scaling
    - Pattern subscriptions for monitoring all runs
    - Easy load balancing of SSE connections
  4. Enhanced Features
    - Redis Streams for replay capability
    - TTL on channels for automatic cleanup
    - Lua scripts for atomic operations
    - Built-in rate limiting with Redis

  Migration Strategy

  1. Phase 1: Add Redis alongside current system
    - Agent publishes to both stdout and Redis
    - New SSE endpoint uses Redis, old uses kubectl
    - A/B test reliability
  2. Phase 2: Redis primary, kubectl fallback
    - SSE primarily from Redis
    - kubectl logs for debugging only
    - Monitor for issues
  3. Phase 3: Redis only
    - Remove kubectl streaming code
    - Simplify orchestrator
    - Add Redis Streams for persistence

  Considerations

  Pros:
  - Massive complexity reduction
  - Better failure isolation
  - Native streaming capabilities
  - Battle-tested at scale

  Cons:
  - New infrastructure dependency
  - Need Redis client in agent container
  - Requires Redis deployment in K8s

  Security:
  - Redis ACLs for channel isolation
  - TLS for Redis connections
  - No shell command execution risks

  This architecture would eliminate most of the edge cases and provide a much
  more robust streaming solution. The kubectl dependency is the weakest link in
   the current system - Redis pub/sub is designed exactly for this use case.
  Elegant and simple, this solution would be.

