"""Add updated_at columns to runs and agent_outputs tables

Revision ID: 26108aff6510
Revises: 011
Create Date: 2025-07-12 20:00:26.066188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26108aff6510'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columns and indexes already added manually, this migration records the change
    pass


def downgrade() -> None:
    op.drop_index('ix_agent_outputs_updated_at', table_name='agent_outputs')
    op.drop_index('ix_runs_updated_at', table_name='runs')
    op.drop_column('agent_outputs', 'updated_at')
    op.drop_column('runs', 'updated_at')