"""Add usage tracking columns to api_keys table

Revision ID: 003
Revises: 002
Create Date: 2025-07-10 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add usage tracking columns to api_keys table."""
    # Add total_requests column
    op.add_column("api_keys", sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"))

    # Add total_runs column
    op.add_column("api_keys", sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    """Remove usage tracking columns from api_keys table."""
    op.drop_column("api_keys", "total_runs")
    op.drop_column("api_keys", "total_requests")
