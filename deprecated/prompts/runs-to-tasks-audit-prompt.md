# 🔍 AIdeator Runs→Tasks Migration Audit – Prompt for New Thread

You are the **"Migration Auditor"**.
Our repository just migrated from the legacy *Run/AgentOutput* schema to the new *Task/TaskOutput* schema (Phases 1-2 complete).
We need a focused sanity-check to make sure there are **no stragglers** and that everything still works from unit tests to Kubernetes job naming.

## Your mission

1. **Source-code sweep**
   * Search for any remaining references to:
     * `Run`, `RunStatus`, `AgentOutput`
     * `run_id` labels, env-vars, DB fields, API params, logs, comments
   * Flag each occurrence with file + line number and a short fix suggestion.

2. **Kubernetes template & env contract**
   * Confirm that `infra/k8s/jobs/agent-job-template.yaml` (and any other templates) now name jobs & labels as
     `task-{task_id}-{variation_id}` **only** (no random hash / run-id).
   * Ensure env vars passed to the container are `TASK_ID`+`VARIATION_ID` – **no RUN_ID**.

3. **Python / FastAPI layer**
   * Verify every API router imports `Task`, `TaskStatus` rather than legacy models.
   * Make sure `/runs` routes & schemas are deleted/not mounted.
   * Check `OutputWriter`, `DatabaseService`, `AgentOrchestrator` behave with `task_id` exclusively.

4. **Frontend**
   * Look for props / hooks that still expect `run_id` and recommend renames.
   * Confirm all fetches call `/api/v1/tasks`* routes.

5. **Tests & scripts**
   * Run `pytest -q`, `npm run test`, Playwright smoke test (`npm run test:e2e -- --grep smoke`) – output pass/fail counts.
   * Grep validation scripts (e.g. `validate_error_handling.sh`) for "run_id".

6. **Database**
   * Alembic head must be revision `002` (unified tasks).
   * Confirm no code writes to `runs` / `agent_outputs`.
   * Confirm sequence `runs_task_id_seq` is unused.

7. **Quick functional check**
   * `tilt up` then POST a new task to `/api/v1/tasks` and poll `/tasks/{id}/outputs`.
   * Report if logs flow and job name matches `task-{id}-0`.

## Deliverables

* **Table** of all straggler findings – file, line, problem, fix.
* **Pass/Fail summary** of each check above.
* **Ordered todo list** of concrete code changes (small PR sized).
* If nothing major is found, state "No blockers – migration gate can be removed."

Keep it concise but complete.  Output in Markdown.  End with a short Yoda quote.