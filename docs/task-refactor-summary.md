# Task Migration – Phase 1 (Core model & DB layer)

Date : 2025-07-16

What was completed
------------------
1. **Model exports**
   • `Task`, `TaskOutput` are now re-exported from `app.models.__init__` – Alembic and FastAPI "see" the new tables.

2. **DatabaseService upgrades**
   • Imported `Task`, `TaskOutput`, `TaskStatus`
   • Added helpers `get_task_by_id()` and `get_task_by_internal_run_id()`
   • Introduced canonical `write_task_output()` that writes to **task_outputs**.
   • Legacy `write_agent_output()` kept as thin wrapper → delegates to new method.
   • No behavioural change for existing callers – but new code can call the task API directly.

3. **OutputWriter alignment**
   • `initialize()` now works because the new DB helpers exist.
   • All writes go through `write_task_output()`.

4. **Back-compat provided**
   • Nothing else broke – legacy calls still compile/run.
   • Next phases can gradually replace `Run` / `AgentOutput` usages.

Next phases
-----------
* Service layer refactor (`AgentOrchestrator`, status updates)
* API routes & schemas (`/tasks` only, remove `/runs`)
* Agent env-var contract (`TASK_ID` only)
* Front-end hooks / pages
* Delete migration‐gate & apply Alembic 002

"Step by step, migrate we must." – Yoda