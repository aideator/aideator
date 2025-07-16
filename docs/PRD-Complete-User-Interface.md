# PRD: AIdeator Task Interface - Complete User Experience

## Overview

A two-page interface for submitting AI agent tasks and monitoring their execution, modeled after OpenAI Codex's background processing workflow. Users submit tasks on the main page and monitor real-time progress on dedicated task detail pages.

## Product Goals

### Primary Objectives
- **Immediate Task Submission**: Users can quickly submit GitHub repository analysis tasks
- **Real-time Progress Monitoring**: Live feedback during agent execution
- **Multi-Agent Comparison**: Side-by-side comparison of different AI approaches
- **Actionable Results**: Direct integration with GitHub for PR creation

### Success Metrics
- Task submission to first feedback: < 30 seconds
- Real-time update latency: < 250ms
- Zero data loss during navigation
- Clear completion signals for all variations

## User Flow Architecture

### Page 1: Main Dashboard (`/`)

#### Task Submission Interface
```
┌─────────────────────────────────────────┐
│ 🚀 Submit New Task                      │
├─────────────────────────────────────────┤
│ GitHub Repository URL                    │
│ [https://github.com/user/repo          ]│
│                                         │
│ Task Description                        │
│ [Analyze this codebase and add tests   ]│
│                                         │
│ Number of Variations: [3] ▼             │
│ Model: [gpt-4o-mini] ▼                  │
│                                         │
│           [Submit Task]                 │
└─────────────────────────────────────────┘
```

**Input Fields**:
- **GitHub URL**: Direct repository link for analysis
- **Task Description**: Natural language prompt (e.g., "Add error handling", "Refactor auth system")
- **Variations**: 1-6 parallel agent executions (default: 3)
- **Model Selection**: gpt-4o-mini, claude-3-5-sonnet, etc.

**Submit Behavior**: 
- Immediate redirect to `/task/{run_id}`
- Background container spawning begins
- No waiting or loading states

#### Task History Dashboard
```
┌─────────────────────────────────────────┐
│ 📋 Recent Tasks                         │
├─────────────────────────────────────────┤
│ 🟢 fastapi/fastapi - Add error handling │
│    3 variations • Complete • 2 min ago  │
│                                         │
│ 🟡 user/repo - Refactor auth system     │
│    3 variations • Running • 1 hour ago  │
│                                         │
│ 🔴 other/repo - Add tests               │
│    3 variations • Failed • 3 hours ago  │
│                                         │
│ ⚪ myapp/backend - Performance audit    │
│    3 variations • Starting • Just now   │
└─────────────────────────────────────────┘
```

**Task List Features**:
- **Status Indicators**: 
  - 🟢 Complete (all variations finished)
  - 🟡 Running (some variations active)
  - 🔴 Failed (critical errors)
  - ⚪ Starting (containers launching)
- **Repository Context**: Owner/repo name displayed
- **Task Summary**: User's original prompt
- **Metadata**: Variation count, status, timestamp
- **Click Navigation**: Any task → `/task/{run_id}`

---

### Page 2: Task Detail & Monitoring (`/task/{run_id}`)

#### Task Header
```
┌─────────────────────────────────────────┐
│ ← Back to Tasks                         │
│                                         │
│ 📁 user/repo - Add error handling       │
│ Submitted: 2 minutes ago                │
│ Status: 🟡 Running (2/3 complete)       │
└─────────────────────────────────────────┘
```

#### Variation Selection
```
┌─────────────────────────────────────────┐
│ [Variation 1 ✅] [Variation 2 🟡] [Variation 3 ⚪] │
└─────────────────────────────────────────┘
```

**Variation Tab States**:
- **⚪ Starting**: Container launching, no logs yet
- **🟡 Running**: Active execution, logs streaming
- **✅ Complete**: Summary received, execution finished
- **🔴 Failed**: Container failed to start or crashed

#### Content Organization (Per Variation)
```
┌─────────────────────────────────────────┐
│ [Logs] [Summary] [Diffs] [Errors]       │
├─────────────────────────────────────────┤
│                                         │
│     Tab Content Area                    │
│     (Real-time updates)                 │
│                                         │
└─────────────────────────────────────────┘
```

##### Logs Tab (Default Active)
**Purpose**: Real-time agent execution monitoring
**Content**:
- All agent output (`stdout`, `stderr`, `logging`)
- Auto-scrolling terminal-style display
- Monospace font with syntax highlighting
- Live streaming indicator during active execution

**Empty States**:
- Starting: "Starting... (agents are being created)"
- No Activity: "No logs yet - agents are starting up..."
- Timeout: "Something went wrong (no activity for 3+ minutes)"

##### Summary Tab
**Purpose**: Completion detection and final results
**Content**:
- 3-line agent completion summary
- "✅ Complete" indicator when present
- Primary signal for task completion

**Empty States**:
- Pre-completion: "No summary yet - agent still analyzing..."
- Failed: "Agent container failed to start"

##### Diffs Tab  
**Purpose**: Code changes and actionable results
**Content**:
- File diffs in unified format
- Syntax highlighting
- Collapsible file sections
- **[Create PR]** button for GitHub integration

**Empty States**:
- Pre-completion: "No diffs yet - no code changes generated..."
- No Changes: "No code changes were made"

**Actions**:
- **Create PR**: Generate pull request using this variation's changes
- **Download**: Export changes as patch file

##### Errors Tab
**Purpose**: Error isolation and debugging
**Content**:
- Filtered `stderr` output
- Error-level logging messages
- Stack traces and diagnostics

**Empty States**:
- No Errors: "No errors - everything running smoothly!"

## Real-time State Management

### Polling Architecture
- **Frequency**: 250ms intervals
- **Endpoint**: `/api/v1/tasks/{run_id}/outputs?since={timestamp}`
- **Strategy**: Incremental updates using timestamp cursors
- **Resilience**: Silent retry on network failures

### Completion Detection
- **Signal**: `summary` output type appears in database
- **Per-Variation**: Independent completion tracking
- **Overall Task**: Complete when all variations have summaries
- **Polling End**: Stop when all variations complete or fail

### State Persistence
- **Database-Driven**: All state lives in PostgreSQL
- **Navigation-Safe**: Page refresh preserves current state
- **Network-Resilient**: Graceful handling of connection issues
- **Historical Access**: Old tasks remain browsable indefinitely

## Error Handling Specifications

### Container Failure Scenarios
**Image Pull Errors**: "Agent container failed to start"
**Resource Constraints**: "Agent container failed to start"  
**Permission Issues**: "Agent container failed to start"
**Timeout Detection**: 3 minutes without logs → "Something went wrong"

### Network Failure Handling
**Polling Failures**: Silent ignore, wait for next interval
**Display**: No user-visible error indicators
**Recovery**: Automatic resume on connectivity restoration

### User Experience Continuity
**Navigation**: Can leave/return without data loss
**Tab Switching**: Instant response using cached data
**Refresh Behavior**: Restore to current database state

## Technical Implementation

### Backend Requirements
- Agent containers write completion summary before exit
- Incremental output API with timestamp filtering
- Kubernetes job status monitoring
- Database indexing on timestamp fields

### Frontend Requirements
- React-based task detail page with real-time updates
- Tab component with variation switching
- Syntax highlighting for code diffs
- GitHub integration for PR creation

### Infrastructure Dependencies
- Kubernetes cluster for agent execution
- PostgreSQL for state persistence
- GitHub API access for PR generation
- Container registry for agent images

## Success Criteria

### Functional Requirements
✅ Users can submit tasks and see immediate feedback
✅ Real-time logs stream with <250ms latency
✅ Clear completion signals for each variation
✅ Multi-variation comparison workflow
✅ Direct PR creation from results

### Non-Functional Requirements
✅ Handles network interruptions gracefully
✅ Supports 10+ concurrent monitoring sessions
✅ Zero data loss during navigation
✅ Works on mobile and desktop browsers

### User Experience Validation
✅ Task submission feels immediate and responsive
✅ Progress monitoring provides confidence and engagement
✅ Results exploration enables informed decision-making
✅ GitHub integration creates actionable outcomes

---

**This PRD defines the complete user experience for AIdeator's task submission and monitoring interface, providing OpenAI Codex-style background processing with multi-agent comparison capabilities.**