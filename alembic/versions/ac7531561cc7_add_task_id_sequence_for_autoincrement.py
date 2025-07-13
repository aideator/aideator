"""add task_id sequence for autoincrement

Revision ID: ac7531561cc7
Revises: 012
Create Date: 2025-07-13 03:53:53.156421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac7531561cc7'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing sequence for task_id autoincrement."""
    
    # Create sequence if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'runs_task_id_seq') THEN
                -- Create the sequence
                CREATE SEQUENCE runs_task_id_seq;
                
                -- Set the current value based on existing data
                PERFORM setval('runs_task_id_seq', COALESCE(MAX(task_id), 0) + 1, false) FROM runs;
                
                -- Set the column default to use the sequence  
                ALTER TABLE runs ALTER COLUMN task_id SET DEFAULT nextval('runs_task_id_seq');
                
                -- Set sequence ownership
                ALTER SEQUENCE runs_task_id_seq OWNED BY runs.task_id;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove the task_id sequence."""
    
    # Remove the default value
    op.execute("ALTER TABLE runs ALTER COLUMN task_id DROP DEFAULT;")
    
    # Drop the sequence if it exists
    op.execute("DROP SEQUENCE IF EXISTS runs_task_id_seq;")