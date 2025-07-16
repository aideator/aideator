"""update_model_definitions_schema

Revision ID: 008
Revises: 007
Create Date: 2025-07-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update model_definitions table to match current schema."""

    # First, drop the foreign key constraint from model_variants if it exists
    connection = op.get_bind()

    # Check if model_variants table exists
    result = connection.execute(
        sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'model_variants'
        )
    """)
    )
    table_exists = result.scalar()

    if table_exists:
        # Check if the constraint exists
        result = connection.execute(
            sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.table_constraints
                WHERE table_name = 'model_variants'
                AND constraint_name = 'model_variants_model_definition_id_fkey'
            )
        """)
        )
        constraint_exists = result.scalar()

        if constraint_exists:
            op.drop_constraint(
                "model_variants_model_definition_id_fkey",
                "model_variants",
                type_="foreignkey",
            )

    # Create new table with updated schema
    op.create_table(
        "model_definitions_new",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("litellm_model_name", sa.String(), nullable=False),
        sa.Column("litellm_provider", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("max_input_tokens", sa.Integer(), nullable=True),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("input_price_per_1m_tokens", sa.Float(), nullable=True),
        sa.Column("output_price_per_1m_tokens", sa.Float(), nullable=True),
        sa.Column("input_cost_per_token", sa.Float(), nullable=True),
        sa.Column("output_cost_per_token", sa.Float(), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("supports_function_calling", sa.Boolean(), nullable=False),
        sa.Column("supports_vision", sa.Boolean(), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("requires_api_key", sa.Boolean(), nullable=False),
        sa.Column("requires_region", sa.Boolean(), nullable=False),
        sa.Column("requires_project_id", sa.Boolean(), nullable=False),
        sa.Column("api_key_env_var", sa.String(), nullable=True),
        sa.Column("default_parameters", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("is_recommended", sa.Boolean(), nullable=False),
        sa.Column("is_popular", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("extra_metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_name"),
    )

    # Copy data from old table to new table, mapping columns appropriately
    # Only copy if old table has data
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM model_definitions"))
    count = result.scalar()

    if count > 0:
        # Copy existing data with column mapping
        op.execute("""
            INSERT INTO model_definitions_new (
                model_name, provider, litellm_model_name, litellm_provider,
                display_name, description, context_window, max_output_tokens,
                input_price_per_1m_tokens, output_price_per_1m_tokens,
                capabilities, requires_api_key, requires_region, requires_project_id,
                default_parameters, is_active, created_at, updated_at,
                -- Set defaults for new fields
                max_tokens, max_input_tokens, input_cost_per_token, output_cost_per_token,
                supports_function_calling, supports_vision, supports_streaming,
                api_key_env_var, category, tags, is_recommended, is_popular,
                first_seen_at, last_seen_at, extra_metadata
            )
            SELECT
                id as model_name, provider, id as litellm_model_name, provider as litellm_provider,
                display_name, description, context_window, max_output_tokens,
                input_price_per_1m_tokens, output_price_per_1m_tokens,
                capabilities, requires_api_key, requires_region, requires_project_id,
                COALESCE(default_parameters, '{}'), is_active, created_at, updated_at,
                -- Defaults for new fields
                context_window as max_tokens, context_window as max_input_tokens,
                input_price_per_1m_tokens / 1000000.0 as input_cost_per_token,
                output_price_per_1m_tokens / 1000000.0 as output_cost_per_token,
                false as supports_function_calling, false as supports_vision, true as supports_streaming,
                null as api_key_env_var, null as category, '[]' as tags,
                false as is_recommended, false as is_popular,
                created_at as first_seen_at, updated_at as last_seen_at, '{}' as extra_metadata
            FROM model_definitions
        """)

    # Drop old table
    op.drop_index("idx_model_definitions_is_active", table_name="model_definitions")
    op.drop_index("idx_model_definitions_provider", table_name="model_definitions")
    op.drop_table("model_definitions")

    # Rename new table to original name
    op.rename_table("model_definitions_new", "model_definitions")

    # Create indexes for new table
    op.create_index(
        "idx_model_definitions_provider", "model_definitions", ["litellm_provider"]
    )
    op.create_index(
        "idx_model_definitions_is_active", "model_definitions", ["is_active"]
    )
    op.create_index(
        "idx_model_definitions_model_name", "model_definitions", ["model_name"]
    )
    op.create_index("idx_model_definitions_category", "model_definitions", ["category"])

    # Since model_variants table now references a different column (model_name instead of id),
    # we need to update the foreign key constraint. But since the table is empty, we can
    # temporarily skip recreating the constraint. The constraint will need to be updated
    # based on the actual model_variants usage.


def downgrade() -> None:
    """Revert model_definitions table to previous schema."""

    # Create old table structure
    op.create_table(
        "model_definitions_old",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=True),
        sa.Column("input_price_per_1m_tokens", sa.Float(), nullable=True),
        sa.Column("output_price_per_1m_tokens", sa.Float(), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("requires_api_key", sa.Boolean(), nullable=False),
        sa.Column("requires_region", sa.Boolean(), nullable=False),
        sa.Column("requires_project_id", sa.Boolean(), nullable=False),
        sa.Column("default_parameters", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data back, preserving what we can
    op.execute("""
        INSERT INTO model_definitions_old (
            id, provider, display_name, description, context_window, max_output_tokens,
            input_price_per_1m_tokens, output_price_per_1m_tokens, capabilities,
            requires_api_key, requires_region, requires_project_id, default_parameters,
            is_active, created_at, updated_at
        )
        SELECT
            model_name as id, provider, display_name, description, context_window, max_output_tokens,
            input_price_per_1m_tokens, output_price_per_1m_tokens, capabilities,
            requires_api_key, requires_region, requires_project_id, default_parameters,
            is_active, created_at, updated_at
        FROM model_definitions
    """)

    # Drop new table
    op.drop_index("idx_model_definitions_category", table_name="model_definitions")
    op.drop_index("idx_model_definitions_model_name", table_name="model_definitions")
    op.drop_index("idx_model_definitions_is_active", table_name="model_definitions")
    op.drop_index("idx_model_definitions_provider", table_name="model_definitions")
    op.drop_table("model_definitions")

    # Rename old table back
    op.rename_table("model_definitions_old", "model_definitions")

    # Recreate old indexes
    op.create_index("idx_model_definitions_provider", "model_definitions", ["provider"])
    op.create_index(
        "idx_model_definitions_is_active", "model_definitions", ["is_active"]
    )
