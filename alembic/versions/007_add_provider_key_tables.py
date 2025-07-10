"""add_provider_key_tables

Revision ID: 007
Revises: 006
Create Date: 2025-01-10 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create provider_api_keys table
    op.create_table("provider_api_keys",
    sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("model_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("encrypted_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("key_hint", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("encryption_version", sa.Integer(), nullable=False),
    sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("is_active", sa.Boolean(), nullable=False),
    sa.Column("is_valid", sa.Boolean(), nullable=True),
    sa.Column("last_validated_at", sa.DateTime(), nullable=True),
    sa.Column("last_used_at", sa.DateTime(), nullable=True),
    sa.Column("last_error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("total_requests", sa.Integer(), nullable=False),
    sa.Column("total_tokens", sa.Integer(), nullable=False),
    sa.Column("total_cost_usd", sa.Float(), nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
    sa.Column("expires_at", sa.DateTime(), nullable=True),
    sa.Column("extra_metadata", sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("user_id", "provider", "model_name", "is_active", name="unique_active_provider_key")
    )

    # Create indexes
    op.create_index("idx_provider_key_lookup", "provider_api_keys", ["user_id", "provider", "is_active"], unique=False)
    op.create_index("idx_provider_key_model", "provider_api_keys", ["user_id", "model_name", "is_active"], unique=False)
    op.create_index(op.f("ix_provider_api_keys_provider"), "provider_api_keys", ["provider"], unique=False)
    op.create_index(op.f("ix_provider_api_keys_user_id"), "provider_api_keys", ["user_id"], unique=False)
    op.create_index(op.f("ix_provider_api_keys_model_name"), "provider_api_keys", ["model_name"], unique=False)
    op.create_index(op.f("ix_provider_api_keys_is_active"), "provider_api_keys", ["is_active"], unique=False)

    # Create provider_api_key_audit_logs table
    op.create_table("provider_api_key_audit_logs",
    sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("provider_key_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("action", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("details", sa.JSON(), nullable=False),
    sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(["provider_key_id"], ["provider_api_keys.id"], ),
    sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    sa.PrimaryKeyConstraint("id")
    )

    # Create audit log indexes
    op.create_index("idx_audit_user_time", "provider_api_key_audit_logs", ["user_id", "created_at"], unique=False)
    op.create_index("idx_audit_key_time", "provider_api_key_audit_logs", ["provider_key_id", "created_at"], unique=False)
    op.create_index(op.f("ix_provider_api_key_audit_logs_user_id"), "provider_api_key_audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_provider_api_key_audit_logs_provider_key_id"), "provider_api_key_audit_logs", ["provider_key_id"], unique=False)


def downgrade() -> None:
    # Drop audit logs table first (due to foreign key constraint)
    op.drop_index(op.f("ix_provider_api_key_audit_logs_provider_key_id"), table_name="provider_api_key_audit_logs")
    op.drop_index(op.f("ix_provider_api_key_audit_logs_user_id"), table_name="provider_api_key_audit_logs")
    op.drop_index("idx_audit_key_time", table_name="provider_api_key_audit_logs")
    op.drop_index("idx_audit_user_time", table_name="provider_api_key_audit_logs")
    op.drop_table("provider_api_key_audit_logs")

    # Drop provider keys table
    op.drop_index(op.f("ix_provider_api_keys_is_active"), table_name="provider_api_keys")
    op.drop_index(op.f("ix_provider_api_keys_model_name"), table_name="provider_api_keys")
    op.drop_index(op.f("ix_provider_api_keys_user_id"), table_name="provider_api_keys")
    op.drop_index(op.f("ix_provider_api_keys_provider"), table_name="provider_api_keys")
    op.drop_index("idx_provider_key_model", table_name="provider_api_keys")
    op.drop_index("idx_provider_key_lookup", table_name="provider_api_keys")
    op.drop_table("provider_api_keys")
