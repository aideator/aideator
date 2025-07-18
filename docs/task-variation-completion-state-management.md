# Task Variation Completion State Management

## Problem Statement

Currently, the AIdeator system lacks proper state management for tracking completion of individual task variations and coordinating overall task completion. This creates several issues:

1. **No variation-level status tracking**: Cannot determine when individual variations (containers) complete
2. **No task completion coordination**: Cannot determine when ALL variations are complete to mark the entire task as done
3. **Frontend polling inefficiency**: Frontend continues polling indefinitely without knowing when to stop
4. **Poor user experience**: No clear indication of per-variation progress or overall task completion

## Current Architecture

### Task-Level Status
- **Database**: `tasks.status` - `TaskStatus.PENDING/RUNNING/COMPLETED/FAILED`
- **Scope**: Entire task (all variations)
- **Problem**: No granular tracking of individual variation completion

### Variation Execution
- **Containers**: Each variation runs in separate container
- **Outputs**: All write to `task_outputs` table with `variation_id`
- **No coordination**: Containers don't communicate completion status

### Frontend Polling
- **Current**: Continuous polling of all endpoints until user navigates away
- **Problem**: No stop condition, inefficient resource usage

## Proposed Solution

### 1. Variation-Level Status Tracking

#### Database Schema Options

**Option A: Extend task_outputs table**
```sql
ALTER TABLE task_outputs ADD COLUMN variation_status VARCHAR(20);
-- Values: 'pending', 'running', 'completed', 'failed'
```

**Option B: Dedicated variation tracking table**
```sql
CREATE TABLE task_variations (
    task_id INT NOT NULL,
    variation_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    PRIMARY KEY (task_id, variation_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

**Recommendation**: Option B (dedicated table) for cleaner separation of concerns

#### Status Values
- `pending`: Variation created but not started
- `running`: Container is executing
- `completed`: All steps finished successfully (outputs + diffs + summary)
- `failed`: Container failed or timed out

### 2. Agent Container Completion Sequence

Each container follows this standardized sequence:

```python
# 1. Mark variation as running
await mark_variation_status(task_id, variation_id, 'running')

# 2. Execute Claude CLI
await run_claude_cli()
await write_outputs(...)

# 3. Generate git diff
await generate_git_diff()
await write_diffs(...)

# 4. Generate summary
await generate_task_summary()
await write_summary(...)

# 5. Mark variation as complete
await mark_variation_status(task_id, variation_id, 'completed')
```

### 3. Task Completion Coordination

#### Coordination Service Architecture

**Option A: Agent Self-Reporting**
- Each container reports completion to database
- Backend API checks completion status on each request
- Simple implementation, polling-based coordination

**Option B: Orchestrator Service**
- Central service monitors all variations
- Updates task status when all complete
- More complex but cleaner coordination

**Option C: Database Triggers**
- Database automatically updates task status when all variations complete
- Minimal application logic but database-dependent

**Recommendation**: Option A for simplicity, can evolve to Option B later

#### Completion Logic
```python
async def check_task_completion(task_id: int):
    """Check if all variations are complete and update task status"""
    
    # Get all variations for this task
    variations = await get_task_variations(task_id)
    
    # Check completion status
    completed_count = sum(1 for v in variations if v.status == 'completed')
    failed_count = sum(1 for v in variations if v.status == 'failed')
    total_count = len(variations)
    
    # Update task status based on variation completion
    if completed_count == total_count:
        await update_task_status(task_id, TaskStatus.COMPLETED)
    elif failed_count > 0 and (completed_count + failed_count) == total_count:
        await update_task_status(task_id, TaskStatus.FAILED)
    # Otherwise, keep as RUNNING
```

### 4. Frontend Polling Strategy

#### Per-Variation Polling Control
```typescript
// New hook for variation status
function useVariationStatus(taskId: string, variationId: number) {
    const [isComplete, setIsComplete] = useState(false)
    const [status, setStatus] = useState<'pending' | 'running' | 'completed' | 'failed'>('pending')
    
    // Poll variation status until complete
    useEffect(() => {
        if (isComplete) return // Stop polling when complete
        
        const interval = setInterval(async () => {
            const variationStatus = await fetchVariationStatus(taskId, variationId)
            setStatus(variationStatus.status)
            
            if (variationStatus.status === 'completed' || variationStatus.status === 'failed') {
                setIsComplete(true)
            }
        }, 1000)
        
        return () => clearInterval(interval)
    }, [taskId, variationId, isComplete])
    
    return { status, isComplete }
}

// Updated existing hooks
function useTaskDiffs(taskId: string, variationId: number) {
    const { isComplete } = useVariationStatus(taskId, variationId)
    
    // Stop polling diffs when variation is complete
    useEffect(() => {
        if (isComplete) return
        // ... existing polling logic
    }, [isComplete])
}
```

#### Task-Level Completion
```typescript
function useTaskDetail(taskId: string) {
    const [taskComplete, setTaskComplete] = useState(false)
    
    // Continue polling task status until all variations complete
    useEffect(() => {
        if (taskComplete) return
        
        const interval = setInterval(async () => {
            const task = await fetchTaskDetail(taskId)
            if (task.status === 'completed' || task.status === 'failed') {
                setTaskComplete(true)
            }
        }, 2000)
        
        return () => clearInterval(interval)
    }, [taskId, taskComplete])
}
```

### 5. API Endpoints

#### New Endpoints
```python
# Get variation status
@router.get("/{task_id}/variations/{variation_id}/status")
async def get_variation_status(task_id: int, variation_id: int):
    """Get completion status for a specific variation"""
    return {
        "task_id": task_id,
        "variation_id": variation_id,
        "status": "completed",
        "started_at": "2024-01-01T12:00:00Z",
        "completed_at": "2024-01-01T12:05:00Z"
    }

# Get all variation statuses for a task
@router.get("/{task_id}/variations/status")
async def get_task_variations_status(task_id: int):
    """Get completion status for all variations of a task"""
    return {
        "task_id": task_id,
        "total_variations": 3,
        "completed_variations": 2,
        "failed_variations": 0,
        "variations": [
            {"variation_id": 1, "status": "completed"},
            {"variation_id": 2, "status": "completed"},
            {"variation_id": 3, "status": "running"}
        ]
    }
```

### 6. UI State Management

#### Progress Indicators
```
Task Status: "Running" (3 variations)
├── Variation 1: ✅ Complete (outputs, diffs, summary ready)
├── Variation 2: ⏳ Running... (generating summary)
└── Variation 3: ✅ Complete (outputs, diffs, summary ready)

Overall Progress: 2/3 variations complete
```

#### Polling Behavior
- **Per-variation**: Stop polling logs/diffs/summary when variation completes
- **Task-level**: Continue polling task status until all variations complete
- **User feedback**: Show progress indicators for each variation

### 7. Error Handling Strategies

#### Partial Completion Scenarios
1. **Some variations succeed, others fail**: 
   - Mark task as `FAILED` but preserve completed variation outputs
   - Display partial results to user with error indicators

2. **Timeout handling**:
   - Set maximum execution time per variation (e.g., 30 minutes)
   - Auto-fail variations that exceed timeout
   - Continue with other variations

3. **Infrastructure failures**:
   - Container crashes, network issues, database connectivity
   - Retry mechanisms for transient failures
   - Graceful degradation for permanent failures

#### User Experience
- Show partial results even when some variations fail
- Clear error messages indicating which variations failed
- Option to retry failed variations individually

### 8. Implementation Phases

#### Phase 1: Basic Variation Tracking
- Add `task_variations` table
- Update agent containers to report completion
- Add basic API endpoints for variation status

#### Phase 2: Frontend Integration
- Update hooks to use variation status
- Implement smart polling with stop conditions
- Add progress indicators to UI

#### Phase 3: Advanced Coordination
- Implement task completion coordination
- Add retry mechanisms for failed variations
- Enhanced error handling and user feedback

#### Phase 4: Optimizations
- Database triggers for automatic status updates
- Real-time notifications instead of polling
- Performance optimizations for large-scale usage

### 9. Testing Strategy

#### Unit Tests
- Variation status tracking logic
- Task completion coordination
- Frontend polling behavior

#### Integration Tests
- End-to-end variation completion flow
- Multiple variation scenarios
- Error handling paths

#### Performance Tests
- Polling efficiency under load
- Database performance with variation tracking
- Memory usage of frontend state management

### 10. Migration Strategy

#### Database Migration
```sql
-- Create new table
CREATE TABLE task_variations (
    task_id INT NOT NULL,
    variation_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    PRIMARY KEY (task_id, variation_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Populate existing tasks
INSERT INTO task_variations (task_id, variation_id, status)
SELECT id, 1, 'completed' FROM tasks WHERE status = 'completed';
```

#### Backward Compatibility
- Existing tasks continue to work without variation tracking
- Gradual rollout of new polling behavior
- Fallback to old behavior if variation data unavailable

---

## Open Questions

1. **Database approach**: Should we use a dedicated table or extend existing tables?
2. **Coordination timing**: When exactly should we check for task completion?
3. **Failure thresholds**: How many variations can fail before marking entire task as failed?
4. **User notifications**: Should we add real-time notifications for completion?
5. **Resource cleanup**: How to handle cleanup of failed/timeout variations?

## Conclusion

This design provides a comprehensive solution for variation-level state management and task completion coordination. The phased approach allows for incremental implementation while maintaining backward compatibility. The key benefits include:

- **Granular tracking**: Know exactly when each variation completes
- **Efficient polling**: Stop polling when data is ready
- **Better UX**: Clear progress indicators and completion states
- **Robust error handling**: Graceful handling of partial failures
- **Scalable architecture**: Foundation for future enhancements

Implementation should begin with Phase 1 (basic tracking) and evolve based on user feedback and system requirements.