"""Add unified tasks and task_outputs tables

Revision ID: 002
Revises: 001
Create Date: 2025-07-16 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### Drop legacy tables first ###
    # Drop agent_outputs table (replaced by task_outputs)
    op.drop_index(op.f("ix_agent_outputs_timestamp"), table_name="agent_outputs")
    op.drop_index(op.f("ix_agent_outputs_variation_id"), table_name="agent_outputs")
    op.drop_index(op.f("ix_agent_outputs_task_id"), table_name="agent_outputs")
    op.drop_table("agent_outputs")
    
    # Drop runs table (replaced by tasks)
    op.drop_index(op.f("ix_runs_user_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_task_status"), table_name="runs")
    op.drop_index(op.f("ix_runs_status"), table_name="runs")
    op.drop_index(op.f("ix_runs_run_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_github_url"), table_name="runs")
    op.drop_index(op.f("ix_runs_created_at"), table_name="runs")
    op.drop_table("runs")
    op.execute("DROP SEQUENCE IF EXISTS runs_task_id_seq")

    # ### Create tasks table ###
    op.create_table("tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("github_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("agent_mode", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("variations", sa.Integer(), nullable=False),
        sa.Column("model_configs", sa.JSON(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("total_tokens_used", sa.Integer(), nullable=True),
        sa.Column("total_cost_usd", sa.Float(), nullable=True),
        sa.Column("internal_run_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    
    # Create indexes for tasks table
    op.create_index(op.f("ix_tasks_github_url"), "tasks", ["github_url"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_created_at"), "tasks", ["created_at"], unique=False)
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"], unique=False)

    # ### Create task_outputs table ###
    op.create_table("task_outputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("output_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    
    # Create indexes for task_outputs table
    op.create_index(op.f("ix_task_outputs_task_id"), "task_outputs", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_outputs_variation_id"), "task_outputs", ["variation_id"], unique=False)
    op.create_index(op.f("ix_task_outputs_timestamp"), "task_outputs", ["timestamp"], unique=False)


def downgrade() -> None:
    # ### Drop unified tables ###
    op.drop_index(op.f("ix_task_outputs_timestamp"), table_name="task_outputs")
    op.drop_index(op.f("ix_task_outputs_variation_id"), table_name="task_outputs")
    op.drop_index(op.f("ix_task_outputs_task_id"), table_name="task_outputs")
    op.drop_table("task_outputs")
    
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_created_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_github_url"), table_name="tasks")
    op.drop_table("tasks")
    
    # ### Recreate legacy tables ###
    # Recreate runs table with sequence
    op.execute("CREATE SEQUENCE runs_task_id_seq")
    op.create_table("runs",
        sa.Column("task_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("github_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("prompt", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("variations", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("task_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("agent_config", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("total_tokens_used", sa.Integer(), nullable=True),
        sa.Column("total_cost_usd", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("task_id")
    )
    op.execute("ALTER TABLE runs ALTER COLUMN task_id SET DEFAULT nextval('runs_task_id_seq')")
    op.execute("ALTER SEQUENCE runs_task_id_seq OWNED BY runs.task_id")
    
    # Recreate indexes for runs
    op.create_index(op.f("ix_runs_created_at"), "runs", ["created_at"], unique=False)
    op.create_index(op.f("ix_runs_github_url"), "runs", ["github_url"], unique=False)
    op.create_index(op.f("ix_runs_run_id"), "runs", ["run_id"], unique=True)
    op.create_index(op.f("ix_runs_status"), "runs", ["status"], unique=False)
    op.create_index(op.f("ix_runs_task_status"), "runs", ["task_status"], unique=False)
    op.create_index(op.f("ix_runs_user_id"), "runs", ["user_id"], unique=False)
    
    # Recreate agent_outputs table
    op.create_table("agent_outputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("output_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["runs.task_id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_agent_outputs_task_id"), "agent_outputs", ["task_id"], unique=False)
    op.create_index(op.f("ix_agent_outputs_variation_id"), "agent_outputs", ["variation_id"], unique=False)
    op.create_index(op.f("ix_agent_outputs_timestamp"), "agent_outputs", ["timestamp"], unique=False)