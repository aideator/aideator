"""Add agent_outputs table

Revision ID: 010
Revises: 009
Create Date: 2025-07-11 01:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create agent_outputs table."""
    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("output_type", sa.String(), nullable=False, default="stdout"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # Create indexes for efficient querying
    op.create_index("idx_agent_outputs_run_id", "agent_outputs", ["run_id"])
    op.create_index("idx_agent_outputs_variation_id", "agent_outputs", ["variation_id"])
    op.create_index("idx_agent_outputs_timestamp", "agent_outputs", ["timestamp"])
    op.create_index("idx_agent_outputs_output_type", "agent_outputs", ["output_type"])


def downgrade() -> None:
    """Drop agent_outputs table."""
    op.drop_table("agent_outputs")