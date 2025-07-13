# PRD: Real-time Task Monitoring with State Management and UI Flows

## Overview

Enable real-time monitoring of containerized AI agent tasks through a database-driven polling architecture that provides immediate feedback, progressive result display, and clear completion signals.

## Problem Statement

Users need to monitor the progress of long-running AI agent tasks that execute in background containers. The system must provide real-time feedback without complex WebSocket infrastructure while handling various failure modes gracefully.

## Goals

### Primary Goals
- **Immediate Feedback**: Users see task status immediately upon submission
- **Progressive Display**: Results populate as agents produce output
- **Reliable Monitoring**: Robust to network issues and container failures
- **Clear Completion**: Definitive signals when agents finish

### Success Metrics
- Tasks show "Starting..." state within 1 second of submission
- First agent logs appear within 30 seconds of container startup
- 250ms maximum latency for new output display
- Zero data loss during navigation or network interruptions

## User Stories

### Core Monitoring Flow
```
As a user, when I submit a task with 3 variations
I want to immediately see 3 tabs (Variation 1, 2, 3) 
So that I can monitor each agent independently
```

```
As a user, when agents are starting up
I want to see "Starting..." messages in empty tabs
So that I know the system is working on my request
```

```
As a user, when agents begin producing output
I want to see real-time logs streaming in
So that I can follow the agent's thought process
```

```
As a user, when an agent completes its work
I want to see a completion indicator and final summary
So that I know the task is finished
```

### Error Handling
```
As a user, when a container fails to start
I want to see "Agent container failed to start" 
So that I know this variation won't produce results
```

```
As a user, when no logs appear after 3 minutes
I want to see "Something went wrong"
So that I'm not waiting indefinitely
```

## Technical Specification

### Database Schema
```sql
-- Existing agent_outputs table structure
agent_outputs (
  id,
  run_id,
  variation_id,  -- 0, 1, 2 for 3 variations
  content,
  output_type,   -- 'stdout', 'stderr', 'logging', 'summary', 'diffs'
  timestamp
)
```

### API Endpoints
```http
GET /api/v1/tasks/{run_id}/outputs?since={timestamp}&variation_id={id}&output_type={type}
- Returns incremental outputs since timestamp
- Filters by variation and/or output type
- Ordered by timestamp ascending
```

### Frontend State Management

#### Task Lifecycle States
1. **Enqueued**: Task created in runs table
2. **Starting**: Containers being created (show "Starting...")
3. **Running**: Logs appearing (show real output)  
4. **Completed**: Summary exists (show completion indicator)
5. **Failed**: Container failed (show error message)

#### Tab Structure
- **Logs Tab (Default)**: All output types (`stdout`, `stderr`, `logging`)
- **Summary Tab**: `summary` output type only
- **Diffs Tab**: `diffs` output type only
- **Errors Tab**: `stderr` + error-level `logging` messages

#### Polling Strategy
```javascript
// Poll every 250ms
setInterval(async () => {
  const newOutputs = await fetch(
    `/api/v1/tasks/${runId}/outputs?since=${lastTimestamp}`
  )
  updateUI(newOutputs)
  lastTimestamp = getLatestTimestamp(newOutputs)
}, 250)
```

## UI/UX Specifications

### Layout
```
┌─────────────────────────────────────────┐
│ Task: run-abc123                        │
├─────────────────────────────────────────┤
│ [Variation 1] [Variation 2] [Variation 3]│
├─────────────────────────────────────────┤
│ [Logs] [Summary] [Diffs] [Errors]      │
├─────────────────────────────────────────┤
│                                         │
│ Tab Content Area                        │
│ (Streaming logs, completion status,     │
│  error messages, etc.)                  │
│                                         │
└─────────────────────────────────────────┘
```

### State Messages

#### Empty States
- **Starting**: "Starting... (agents are being created)"
- **No Logs Yet**: "No logs yet - agents are starting up..."
- **No Summary Yet**: "No summary yet - agent still analyzing..."
- **No Diffs Yet**: "No diffs yet - no code changes generated..."
- **No Errors**: "No errors - everything running smoothly!"

#### Error States
- **Container Failed**: "Agent container failed to start"
- **Timeout**: "Something went wrong (no activity for 3+ minutes)"

#### Completion States
- **Logs Complete**: Continue showing all logs
- **Summary Complete**: Show 3-line summary + "✅ Complete" indicator
- **Overall Complete**: When all variations have summaries

### Visual Indicators
- **Live Indicator**: Pulsing dot when actively receiving updates
- **Completion Badge**: Green checkmark when summary exists
- **Error Badge**: Red X for failed containers
- **Progress Indicator**: Subtle animation during active polling

## Error Handling

### Container Failures
**Scenario**: Kubernetes job fails to start (ImagePull, RBAC, resources)
**Detection**: No logs after 3 minutes + job status check
**Display**: "Agent container failed to start" (permanent message)
**Action**: No retry, user can restart task manually

### Network Failures
**Scenario**: Polling request fails (network drop, server error)
**Detection**: Fetch promise rejection
**Display**: No user-visible error
**Action**: Silent ignore, wait for next poll interval

### Data Consistency
**Scenario**: User navigates away and returns
**Detection**: Page reload or route change
**Display**: Restore to current state based on database
**Action**: Poll from last timestamp in database

## Implementation Phases

### Phase 1: Core Polling (Week 1)
- [ ] Task detail page with 3 variation tabs
- [ ] Basic polling every 250ms
- [ ] Display logs in real-time
- [ ] Empty state messages

### Phase 2: Completion Detection (Week 1)
- [ ] Summary output type handling
- [ ] Completion indicators
- [ ] Stop polling when all variations complete

### Phase 3: Error Handling (Week 2)
- [ ] Container failure detection
- [ ] Timeout handling (3 minutes)
- [ ] Network failure resilience

### Phase 4: Polish (Week 2)
- [ ] Live indicators
- [ ] Navigation state preservation  
- [ ] Performance optimization
- [ ] Error and diff tab filtering

## Dependencies

### Backend
- Agent containers must write summary on completion
- API endpoints for incremental output retrieval
- Kubernetes job status monitoring

### Frontend
- Task detail page routing (`/task/{run_id}`)
- Real-time polling infrastructure
- Tab component library

## Risks & Mitigations

### Risk: Database Load
**Mitigation**: Limit polling to active tasks, index agent_outputs by timestamp

### Risk: Stale UI State  
**Mitigation**: Database is source of truth, stateless frontend design

### Risk: Poor Performance on Slow Networks
**Mitigation**: Incremental updates, graceful degradation for network failures

## Success Criteria

### Functional
- [ ] Users can monitor 3 agents simultaneously
- [ ] Real-time logs appear within 250ms
- [ ] Clear completion signals for each variation
- [ ] Graceful handling of all error scenarios

### Non-Functional  
- [ ] 250ms average polling latency
- [ ] Works reliably on mobile networks
- [ ] Zero data loss during navigation
- [ ] Handles 10+ concurrent monitoring sessions

---
*This PRD defines the MVP for real-time task monitoring. Future enhancements may include WebSocket streaming, advanced filtering, and multi-user collaboration features.*