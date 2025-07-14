"""Add litellm_analytics table for detailed LLM analytics tracking

Revision ID: 014
Revises: 013
Create Date: 2025-07-13 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create litellm_analytics table."""
    op.create_table(
        "litellm_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=False),
        # Request metadata
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        # Token usage
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        # Cost tracking
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("input_cost_per_token", sa.Float(), nullable=True),
        sa.Column("output_cost_per_token", sa.Float(), nullable=True),
        # Performance metrics
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("time_to_first_token_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_per_second", sa.Float(), nullable=True),
        # Request details
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("stream", sa.Boolean(), nullable=False, default=False),
        # Status and errors
        sa.Column("status", sa.String(), nullable=False, default="success"),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("request_start_time", sa.DateTime(), nullable=True),
        sa.Column("request_end_time", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Raw LiteLLM data
        sa.Column(
            "litellm_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        # Constraints
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index("idx_litellm_analytics_run_id", "litellm_analytics", ["run_id"])
    op.create_index(
        "idx_litellm_analytics_variation_id", "litellm_analytics", ["variation_id"]
    )
    op.create_index(
        "idx_litellm_analytics_request_id", "litellm_analytics", ["request_id"]
    )
    op.create_index("idx_litellm_analytics_model", "litellm_analytics", ["model"])
    op.create_index("idx_litellm_analytics_provider", "litellm_analytics", ["provider"])
    op.create_index("idx_litellm_analytics_status", "litellm_analytics", ["status"])
    op.create_index(
        "idx_litellm_analytics_request_start_time",
        "litellm_analytics",
        ["request_start_time"],
    )
    op.create_index(
        "idx_litellm_analytics_created_at", "litellm_analytics", ["created_at"]
    )

    # Composite indexes for common analytics queries
    op.create_index(
        "idx_litellm_analytics_run_variation",
        "litellm_analytics",
        ["run_id", "variation_id"],
    )
    op.create_index(
        "idx_litellm_analytics_model_provider",
        "litellm_analytics",
        ["model", "provider"],
    )
    op.create_index(
        "idx_litellm_analytics_cost_analysis",
        "litellm_analytics",
        ["provider", "model", "cost_usd"],
    )


def downgrade() -> None:
    """Drop litellm_analytics table."""
    op.drop_table("litellm_analytics")
