"""Sync runs table with model

Revision ID: 004
Revises: 003
Create Date: 2025-07-10 16:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing columns to runs table."""

    # Add winning_variation_id column
    op.add_column(
        "runs", sa.Column("winning_variation_id", sa.Integer(), nullable=True)
    )

    # Add started_at column
    op.add_column("runs", sa.Column("started_at", sa.DateTime(), nullable=True))

    # Add agent_config column
    op.add_column(
        "runs",
        sa.Column("agent_config", sa.JSON(), nullable=False, server_default="{}"),
    )

    # Add api_key_id column
    op.add_column("runs", sa.Column("api_key_id", sa.String(), nullable=True))

    # Add results column
    op.add_column(
        "runs", sa.Column("results", sa.JSON(), nullable=False, server_default="{}")
    )

    # Add statistics columns
    op.add_column("runs", sa.Column("total_tokens_used", sa.Integer(), nullable=True))
    op.add_column("runs", sa.Column("total_cost_usd", sa.Float(), nullable=True))

    # Create indexes for new columns
    op.create_index("idx_runs_winning_variation_id", "runs", ["winning_variation_id"])
    op.create_index("idx_runs_api_key_id", "runs", ["api_key_id"])
    op.create_index("idx_runs_started_at", "runs", ["started_at"])
    op.create_index("idx_runs_created_at", "runs", ["created_at"])

    # Add foreign key constraint for api_key_id
    op.create_foreign_key(
        "fk_runs_api_key_id",
        "runs",
        "api_keys",
        ["api_key_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove columns added to runs table."""

    # Drop foreign key constraint
    op.drop_constraint("fk_runs_api_key_id", "runs", type_="foreignkey")

    # Drop indexes
    op.drop_index("idx_runs_created_at", "runs")
    op.drop_index("idx_runs_started_at", "runs")
    op.drop_index("idx_runs_api_key_id", "runs")
    op.drop_index("idx_runs_winning_variation_id", "runs")

    # Drop columns
    op.drop_column("runs", "total_cost_usd")
    op.drop_column("runs", "total_tokens_used")
    op.drop_column("runs", "results")
    op.drop_column("runs", "api_key_id")
    op.drop_column("runs", "agent_config")
    op.drop_column("runs", "started_at")
    op.drop_column("runs", "winning_variation_id")
