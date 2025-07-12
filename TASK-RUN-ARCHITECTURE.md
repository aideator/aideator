# Task-Run Architecture Documentation

## Overview

AIdeator uses a **decoupled background processing architecture** similar to:
- **OpenAI Codex background agents** (the current coding feature, not the old language model)
- **Cursor.com background agents**

This architecture separates task submission from task monitoring, allowing users to submit work and check progress independently.

## Workflow Architecture

### 1. Task Creation Flow (Main Page)
```
User Input → POST /api/v1/runs → runs table → Kubernetes Jobs → Background Processing
```

**Process:**
1. User enters task description on main page
2. Frontend calls `POST /api/v1/runs` with:
   - Repository URL
   - Task prompt
   - Number of variations
3. API creates entry in `runs` table
4. API fires off Kubernetes jobs (one per variation)
5. Jobs run independently in background

### 2. Background Processing
```
Kubernetes Jobs → Write to agent_outputs table → Continue processing
```

**Process:**
1. Each Kubernetes job runs its assigned variation
2. Jobs write all outputs directly to SQL (`agent_outputs` table):
   - stdout/stderr logs
   - Status updates
   - Code diffs
   - Summaries
   - Additional info
3. Jobs complete independently
4. No direct communication back to frontend

### 3. Task Monitoring Flow (Task Detail Page)
```
User Navigation → GET /api/v1/tasks/{task_id} → Read agent_outputs → Display Progress
```

**Process:**
1. User clicks on task from task list
2. Frontend navigates to `/task/{task_id}` page
3. Frontend calls task detail API endpoints
4. API reads from `agent_outputs` table for that task
5. Frontend displays real-time progress, logs, and results

## API Structure

### Task Creation APIs
- `POST /api/v1/runs` - Create new task and fire Kubernetes jobs
  - Input: repository, prompt, variations
  - Output: run_id, job status
  - Side effect: Creates Kubernetes jobs

### Task Monitoring APIs  
- `GET /api/v1/tasks` - List all tasks for main page (maps to runs table)
- `GET /api/v1/tasks/{task_id}` - Get task details and progress
- `GET /api/v1/tasks/{task_id}/outputs` - Get agent outputs for a task
- `GET /api/v1/tasks/{task_id}/variations/{variation_id}/outputs` - Get outputs for specific variation

## Database Schema

### Core Tables
1. **`runs`** - Task metadata and job configuration
   - `id` (task_id/run_id - same thing)
   - `prompt`, `github_url`, `variations`
   - `status`, `task_status`
   - `created_at`, `started_at`, `completed_at`

2. **`agent_outputs`** - All agent communication and results
   - `run_id` (foreign key to runs.id)
   - `variation_id` (which agent variation)
   - `content`, `output_type`, `timestamp`

## Key Design Principles

### 1. Task ID = Run ID
- No separate task and run concepts
- The `runs.id` serves as the task identifier
- Simplifies data model and relationships

### 2. No Status Tracking (For Now)
- We don't actively monitor when Kubernetes jobs complete
- Status is inferred from agent outputs
- Jobs may run indefinitely or timeout naturally
- Future enhancement: Add job completion monitoring

### 3. SQL-Centric Communication
- All inter-component communication goes through PostgreSQL
- Agent outputs are the single source of truth
- No direct WebSocket or Redis dependencies for core functionality
- Enables replay, debugging, and historical analysis

### 4. Decoupled Frontend Pages
- **Main Page**: Task creation and high-level task list
- **Task Detail Page**: Deep dive into specific task progress
- Pages are independent and can be developed separately
- No shared state beyond the database

## Frontend Page Structure

### Main Page (`/`)
- Task input form
- Task list (from `runs` table)
- Quick status indicators
- Navigation to task details

### Task Detail Page (`/task/{task_id}`)
- Real-time progress from `agent_outputs`
- Variation comparison (tabbed interface)
- Logs, diffs, and results
- Winner selection and actions

## Implementation Status

### ✅ Completed
- Basic runs table schema
- Agent output logging to SQL
- Kubernetes job execution
- Task creation API

### 🚧 In Progress
- API endpoint restructuring
- Frontend page separation
- Task detail page implementation

### 📋 Todo
- Agent output polling/streaming for task detail page
- Variation comparison UI
- Winner selection functionality
- Historical task browsing

## References

- **OpenAI Codex Background Agents**: The current coding feature in OpenAI's interface
- **Cursor.com Background Agents**: Similar background processing for code tasks
- **Database-First Architecture**: All state lives in PostgreSQL for reliability and debuggability