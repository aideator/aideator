# Task Migration – Phase 2 (Service-Layer Orchestrator)

Date: 2025-07-16

## What was completed
1. **Orchestrator switch**
   `app/services/agent_orchestrator.py` now works exclusively with
   `Task` + `TaskStatus`. All internal status updates target the `tasks`
   table; `Run`/`RunStatus` are no longer imported here.

2. **Status enum replacement**
   Every reference to `RunStatus.*` in the orchestrator was swapped for
   `TaskStatus.*` (`RUNNING`, `COMPLETED`, `FAILED`).

3. **DB update helper**
   `_update_run_status()` now fetches `Task` rows instead of `Run`.

_No other packages were touched in this phase – old API routes & agents
still compile while the new path is being built._

---

## Hand-off – Phase 3 TODO (new thread)

1. **API layer**
   • Remove `/runs` routes, convert controllers & schemas to `Task` / `TaskOutput`.
   • Update dependency injections and services to use new enums.

2. **Agent container**
   • Pass only `TASK_ID` in env; drop `RUN_ID`.
   • Update `agent/core/orchestrator.py` and `OutputWriter` prefixes to use `task_id`.

3. **Kubernetes job template**
   • Rename Job & labels to `task-{task_id}-{variation_id}`
   • Remove RUN_ID arg.

4. **Frontend hooks/pages**
   • Ensure all fetches go through `/tasks` endpoints and rely on `task.id`.

5. **Migrations**
   • After code is clean, delete the migration-gate file and apply Alembic 002.

6. **Cleanup**
   • Remove dead `Run` / `AgentOutput` references, delete models when safe.

"Step by step, migrate we must. – Yoda"