"""add_session_turn_to_runs

Revision ID: 013
Revises: 012
Create Date: 2025-07-13 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add session_id and turn_id columns to runs table."""

    # Add session_id column
    op.add_column("runs", sa.Column("session_id", sa.String(), nullable=True))

    # Add turn_id column
    op.add_column("runs", sa.Column("turn_id", sa.String(), nullable=True))

    # Create indexes for faster lookups
    op.create_index("ix_runs_session_id", "runs", ["session_id"])
    op.create_index("ix_runs_turn_id", "runs", ["turn_id"])


def downgrade() -> None:
    """Remove session_id and turn_id columns from runs table."""

    # Drop indexes
    op.drop_index("ix_runs_turn_id", "runs")
    op.drop_index("ix_runs_session_id", "runs")

    # Drop columns
    op.drop_column("runs", "turn_id")
    op.drop_column("runs", "session_id")
