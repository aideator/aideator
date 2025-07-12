"""Add task_status to runs table

Revision ID: 011
Revises: 010
Create Date: 2025-07-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add task_status column to runs table
    op.add_column('runs', sa.Column('task_status', sa.String(length=20), nullable=False, server_default='open'))
    
    # Add index for task_status for efficient filtering
    op.create_index(op.f('ix_runs_task_status'), 'runs', ['task_status'], unique=False)


def downgrade() -> None:
    # Remove index and column
    op.drop_index(op.f('ix_runs_task_status'), table_name='runs')
    op.drop_column('runs', 'task_status')