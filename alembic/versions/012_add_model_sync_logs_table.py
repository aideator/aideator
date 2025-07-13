"""add_model_sync_logs_table

Revision ID: 012
Revises: 011
Create Date: 2025-07-12 21:25:00.000000

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
    """Add model_sync_logs table for tracking LiteLLM model synchronization."""

    op.create_table(
        "model_sync_logs",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("models_discovered", sa.Integer(), nullable=False, default=0),
        sa.Column("models_added", sa.Integer(), nullable=False, default=0),
        sa.Column("models_updated", sa.Integer(), nullable=False, default=0),
        sa.Column("models_deactivated", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=False, default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop model_sync_logs table."""
    op.drop_table("model_sync_logs")
