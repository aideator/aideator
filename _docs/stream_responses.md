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
