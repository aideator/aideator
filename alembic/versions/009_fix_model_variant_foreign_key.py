"""fix_model_variant_foreign_key

Revision ID: 009
Revises: 008
Create Date: 2025-07-10 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Fix model_variant foreign key to reference model_definitions.model_name instead of id."""

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
        # Drop existing foreign key constraint if it exists
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

        # Add new foreign key constraint referencing model_name
        op.create_foreign_key(
            "model_variants_model_definition_id_fkey",
            "model_variants",
            "model_definitions",
            ["model_definition_id"],
            ["model_name"],
        )
    # Note: If model_variants table doesn't exist, it will be created by SQLModel.metadata.create_all()
    # with the correct schema when the application starts


def downgrade() -> None:
    """Revert foreign key changes."""

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
        # Drop current foreign key constraint
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

        # Recreate foreign key constraint referencing id (this will fail if data types don't match)
        # Note: This downgrade may not work if the model_definitions table still has integer ids
        try:
            op.create_foreign_key(
                "model_variants_model_definition_id_fkey",
                "model_variants",
                "model_definitions",
                ["model_definition_id"],
                ["id"],
            )
        except Exception:
            # If this fails, just leave the constraint dropped
            pass
