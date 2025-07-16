"""Drop legacy runs & agent_outputs tables

Revision ID: 003
Revises: 002
Create Date: 2025-07-17 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove legacy tables now that unified tasks schema is live."""
    # Drop agent_outputs if it still exists
    op.execute(
        "DROP TABLE IF EXISTS agent_outputs CASCADE"
    )
    # Drop runs table
    op.execute(
        "DROP TABLE IF EXISTS runs CASCADE"
    )
    # Drop obsolete sequence
    op.execute(
        "DROP SEQUENCE IF EXISTS runs_task_id_seq"
    )


def downgrade() -> None:
    """Recreate legacy tables (minimal) for downgrade."""
    # Re-create runs table (basic columns so downgrade works)
    op.execute(
        """
        CREATE SEQUENCE runs_task_id_seq START WITH 1;
        """
    )
    op.create_table(
        "runs",
        sa.Column("task_id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.String(), nullable=False, unique=True),
        sa.Column("github_url", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("variations", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("output_type", sa.String(), nullable=False, server_default="stdout"),
    )