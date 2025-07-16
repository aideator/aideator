"""Add task_id system to runs and related tables

Revision ID: 012
Revises: 011
Create Date: 2025-07-12 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add task_id system with proper ordering."""

    # Step 1: Drop all foreign key constraints that depend on runs.id
    op.drop_constraint("agent_outputs_run_id_fkey", "agent_outputs", type_="foreignkey")

    # Check if preferences table exists and has foreign key to runs
    try:
        op.drop_constraint("preferences_run_id_fkey", "preferences", type_="foreignkey")
    except:
        pass  # Constraint might not exist

    # Step 2: Add task_id column to runs table (auto-incrementing)
    # First create sequence
    op.execute("CREATE SEQUENCE runs_task_id_seq")

    # Add column as nullable first (to handle existing data)
    op.add_column("runs", sa.Column("task_id", sa.Integer(), nullable=True))

    # Populate existing rows with sequence values
    op.execute("UPDATE runs SET task_id = nextval('runs_task_id_seq')")

    # Now make it NOT NULL
    op.alter_column("runs", "task_id", nullable=False)

    # Set default value separately
    op.execute("ALTER TABLE runs ALTER COLUMN task_id SET DEFAULT nextval('runs_task_id_seq')")

    # Set sequence ownership
    op.execute("ALTER SEQUENCE runs_task_id_seq OWNED BY runs.task_id")

    # Step 3: Rename current id column to run_id in runs table
    op.alter_column("runs", "id", new_column_name="run_id")

    # Step 4: Update primary key constraint on runs table
    op.drop_constraint("runs_pkey", "runs", type_="primary")
    op.create_primary_key("runs_pkey", "runs", ["task_id"])

    # Step 5: Add unique constraint on run_id
    op.create_unique_constraint("uq_runs_run_id", "runs", ["run_id"])
    op.create_index("ix_runs_run_id", "runs", ["run_id"])

    # Step 6: Add task_id column to agent_outputs table
    op.add_column("agent_outputs", sa.Column("task_id", sa.Integer(), nullable=True))

    # Step 7: Populate task_id in agent_outputs from runs table (if data exists)
    op.execute("""
        UPDATE agent_outputs 
        SET task_id = runs.task_id 
        FROM runs 
        WHERE agent_outputs.run_id = runs.run_id
    """)

    # Step 8: Make task_id NOT NULL in agent_outputs
    op.alter_column("agent_outputs", "task_id", nullable=False)

    # Step 9: Create new foreign key constraint using task_id
    op.create_foreign_key("fk_agent_outputs_task_id", "agent_outputs", "runs", ["task_id"], ["task_id"], ondelete="CASCADE")

    # Step 10: Drop run_id column from agent_outputs
    op.drop_index("idx_agent_outputs_run_id", "agent_outputs")
    op.drop_column("agent_outputs", "run_id")

    # Step 11: Create index on task_id in agent_outputs
    op.create_index("ix_agent_outputs_task_id", "agent_outputs", ["task_id"])


def downgrade() -> None:
    """Reverse the task_id system changes."""

    # Reverse Step 10: Drop task_id index
    op.drop_index("ix_agent_outputs_task_id", "agent_outputs")

    # Reverse Step 9: Add back run_id column to agent_outputs
    op.add_column("agent_outputs", sa.Column("run_id", sa.String(), nullable=True))

    # Populate run_id from runs table
    op.execute("""
        UPDATE agent_outputs 
        SET run_id = runs.run_id 
        FROM runs 
        WHERE agent_outputs.task_id = runs.task_id
    """)

    op.alter_column("agent_outputs", "run_id", nullable=False)
    op.create_index("idx_agent_outputs_run_id", "agent_outputs", ["run_id"])

    # Reverse Step 8: Restore original foreign key
    op.drop_constraint("fk_agent_outputs_task_id", "agent_outputs", type_="foreignkey")
    op.create_foreign_key("agent_outputs_run_id_fkey", "agent_outputs", "runs", ["run_id"], ["run_id"], ondelete="CASCADE")

    # Reverse Step 7 & 6 & 5: Drop task_id from agent_outputs
    op.drop_column("agent_outputs", "task_id")

    # Reverse Step 4: Drop run_id unique constraint and index
    op.drop_index("ix_runs_run_id", "runs")
    op.drop_constraint("uq_runs_run_id", "runs", type_="unique")

    # Reverse Step 3: Restore original primary key
    op.drop_constraint("runs_pkey", "runs", type_="primary")
    op.create_primary_key("runs_pkey", "runs", ["run_id"])

    # Reverse Step 2: Rename run_id back to id
    op.alter_column("runs", "run_id", new_column_name="id")

    # Reverse Step 1: Drop task_id column and sequence
    # Remove default first, then drop column, then sequence
    op.execute("ALTER TABLE runs ALTER COLUMN task_id DROP DEFAULT")
    op.drop_column("runs", "task_id")
    op.execute("DROP SEQUENCE IF EXISTS runs_task_id_seq")
