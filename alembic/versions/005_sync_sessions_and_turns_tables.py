"""Sync sessions and turns tables with models

Revision ID: 005
Revises: 004
Create Date: 2025-07-10 16:35:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing columns to sessions and turns tables."""

    # Add missing columns to sessions table
    op.add_column("sessions", sa.Column("title", sa.String(length=200), nullable=False, server_default="Untitled Session"))
    op.add_column("sessions", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("sessions", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("sessions", sa.Column("last_activity_at", sa.DateTime(), nullable=False, server_default="NOW()"))
    op.add_column("sessions", sa.Column("models_used", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("sessions", sa.Column("total_turns", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("sessions", sa.Column("total_cost", sa.Float(), nullable=False, server_default="0.0"))

    # Rename 'name' to 'title' if it exists (from initial migration)
    # op.alter_column('sessions', 'name', new_column_name='title')

    # Add missing columns to turns table
    op.add_column("turns", sa.Column("turn_number", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("turns", sa.Column("context", sa.Text(), nullable=True))
    op.add_column("turns", sa.Column("models_requested", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("turns", sa.Column("responses", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("turns", sa.Column("started_at", sa.DateTime(), nullable=False, server_default="NOW()"))
    op.add_column("turns", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.add_column("turns", sa.Column("total_cost", sa.Float(), nullable=False, server_default="0.0"))

    # Add missing columns to preferences table
    op.add_column("preferences", sa.Column("preferred_model", sa.String(), nullable=False, server_default=""))
    op.add_column("preferences", sa.Column("preferred_response_id", sa.String(), nullable=False, server_default=""))
    op.add_column("preferences", sa.Column("compared_models", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("preferences", sa.Column("response_quality_scores", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("preferences", sa.Column("feedback_text", sa.Text(), nullable=True))
    op.add_column("preferences", sa.Column("confidence_score", sa.Integer(), nullable=True))
    op.add_column("preferences", sa.Column("preference_type", sa.String(), nullable=False, server_default="response"))

    # Create new indexes
    op.create_index("idx_sessions_title", "sessions", ["title"])
    op.create_index("idx_sessions_is_active", "sessions", ["is_active"])
    op.create_index("idx_sessions_last_activity_at", "sessions", ["last_activity_at"])
    op.create_index("idx_turns_turn_number", "turns", ["turn_number"])
    op.create_index("idx_turns_started_at", "turns", ["started_at"])
    op.create_index("idx_preferences_preferred_model", "preferences", ["preferred_model"])
    op.create_index("idx_preferences_preference_type", "preferences", ["preference_type"])


def downgrade() -> None:
    """Remove columns added to sessions, turns, and preferences tables."""

    # Drop indexes
    op.drop_index("idx_preferences_preference_type", "preferences")
    op.drop_index("idx_preferences_preferred_model", "preferences")
    op.drop_index("idx_turns_started_at", "turns")
    op.drop_index("idx_turns_turn_number", "turns")
    op.drop_index("idx_sessions_last_activity_at", "sessions")
    op.drop_index("idx_sessions_is_active", "sessions")
    op.drop_index("idx_sessions_title", "sessions")

    # Drop columns from preferences
    op.drop_column("preferences", "preference_type")
    op.drop_column("preferences", "confidence_score")
    op.drop_column("preferences", "feedback_text")
    op.drop_column("preferences", "response_quality_scores")
    op.drop_column("preferences", "compared_models")
    op.drop_column("preferences", "preferred_response_id")
    op.drop_column("preferences", "preferred_model")

    # Drop columns from turns
    op.drop_column("turns", "total_cost")
    op.drop_column("turns", "duration_seconds")
    op.drop_column("turns", "started_at")
    op.drop_column("turns", "responses")
    op.drop_column("turns", "models_requested")
    op.drop_column("turns", "context")
    op.drop_column("turns", "turn_number")

    # Drop columns from sessions
    op.drop_column("sessions", "total_cost")
    op.drop_column("sessions", "total_turns")
    op.drop_column("sessions", "models_used")
    op.drop_column("sessions", "last_activity_at")
    op.drop_column("sessions", "is_archived")
    op.drop_column("sessions", "is_active")
    op.drop_column("sessions", "title")
