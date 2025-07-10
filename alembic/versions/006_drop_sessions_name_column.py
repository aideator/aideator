"""Drop sessions name column

Revision ID: 006
Revises: 005
Create Date: 2025-07-10 16:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the old name column from sessions table."""
    
    # Drop the old name column that conflicts with title
    op.drop_column('sessions', 'name')


def downgrade() -> None:
    """Restore the name column."""
    
    # Add back the name column
    op.add_column('sessions', sa.Column('name', sa.String(), nullable=False, server_default='Untitled'))