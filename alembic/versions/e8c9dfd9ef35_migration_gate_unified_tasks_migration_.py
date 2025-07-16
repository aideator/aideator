"""MIGRATION GATE: unified tasks migration blocked pending code completion

Revision ID: e8c9dfd9ef35
Revises: 002
Create Date: 2025-07-16 01:49:09.631254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8c9dfd9ef35'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 🚨 MIGRATION GATE: DO NOT APPLY MIGRATION 002 YET! 🚨
    #
    # This is a placeholder migration that blocks the unified tasks migration (002)
    # from being applied until ALL code has been updated to use the new models.
    #
    # WHY THIS EXISTS:
    # - Migration 002 drops the legacy 'runs' and 'agent_outputs' tables
    # - Current code still depends on these tables in many places
    # - Applying 002 now would break the application
    #
    # BEFORE APPLYING 002, ENSURE:
    # ✅ All imports updated: Run → Task, RunStatus → TaskStatus, AgentOutput → TaskOutput  
    # ✅ All service methods updated: get_run_by_run_id → get_task_by_id
    # ✅ All API endpoints use Task/TaskOutput exclusively
    # ✅ Agent code uses TASK_ID only (no RUN_ID fallback)
    # ✅ Frontend calls /tasks endpoints (not /runs)
    # ✅ Shadow write validation completed successfully
    # ✅ Feature flag tested in dev/staging environments
    #
    # TO PROCEED:
    # 1. Complete all code migration phases (2a-2e)
    # 2. Test with shadow writes (Phase 3)  
    # 3. Delete this migration file
    # 4. Apply migration 002 in controlled deployment
    #
    # See: https://github.com/your-repo/issues/unified-tasks-migration
    
    raise RuntimeError(
        "🚨 MIGRATION 002 IS BLOCKED! 🚨\n\n"
        "The unified tasks migration cannot be applied yet because code migration is incomplete.\n"
        "Current code still depends on legacy 'runs' and 'agent_outputs' tables.\n\n"
        "Complete the code migration phases first:\n"
        "- Phase 2a: Domain models (Task/TaskStatus)\n" 
        "- Phase 2b: Service layer methods\n"
        "- Phase 2c: Agent path (TASK_ID only)\n"
        "- Phase 2d: API layer merge\n"
        "- Phase 2e: Frontend hooks\n"
        "- Phase 3: Shadow write validation\n\n"
        "Only then delete this migration and apply 002.\n"
        "See migration plan documentation for details."
    )


def downgrade() -> None:
    # This migration does nothing, so downgrade is also a no-op
    pass