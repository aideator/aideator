"""add_github_oauth_fields

Revision ID: 010
Revises: 009
Create Date: 2025-07-12 07:40:00.000000

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
    """Add GitHub OAuth fields to users table."""
    # Add GitHub OAuth fields
    op.add_column('users', sa.Column('github_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('github_username', sa.String(), nullable=True))
    op.add_column('users', sa.Column('github_avatar_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('github_access_token_encrypted', sa.String(), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(), nullable=False, server_default='local'))
    
    # Create indexes
    op.create_index(op.f('ix_users_github_id'), 'users', ['github_id'], unique=True)
    op.create_index(op.f('ix_users_github_username'), 'users', ['github_username'], unique=False)


def downgrade() -> None:
    """Remove GitHub OAuth fields from users table."""
    # Drop indexes
    op.drop_index(op.f('ix_users_github_username'), table_name='users')
    op.drop_index(op.f('ix_users_github_id'), table_name='users')
    
    # Drop columns
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'github_access_token_encrypted')
    op.drop_column('users', 'github_avatar_url')
    op.drop_column('users', 'github_username')
    op.drop_column('users', 'github_id')