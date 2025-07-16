"""Current schema from SQLModel definitions

Revision ID: 001
Revises: 
Create Date: 2025-07-15 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create users table ###
    op.create_table('users',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('company', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('max_runs_per_day', sa.Integer(), nullable=False),
        sa.Column('max_variations_per_run', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # ### Removed model_definitions table - no LiteLLM functionality needed ###
    # ### Removed provider_credentials table - not needed in dev mode ###

    # ### Create runs table with sequence ###
    # Create the sequence first
    op.execute("CREATE SEQUENCE runs_task_id_seq")
    
    op.create_table('runs',
        sa.Column('task_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('github_url', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('prompt', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('variations', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('task_status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('agent_config', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error_message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True),
        sa.Column('total_cost_usd', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('task_id')
    )
    
    # Set the sequence as default for task_id and set ownership
    op.execute("ALTER TABLE runs ALTER COLUMN task_id SET DEFAULT nextval('runs_task_id_seq')")
    op.execute("ALTER SEQUENCE runs_task_id_seq OWNED BY runs.task_id")
    
    # Create indexes
    op.create_index(op.f('ix_runs_created_at'), 'runs', ['created_at'], unique=False)
    op.create_index(op.f('ix_runs_github_url'), 'runs', ['github_url'], unique=False)
    op.create_index(op.f('ix_runs_run_id'), 'runs', ['run_id'], unique=True)
    op.create_index(op.f('ix_runs_status'), 'runs', ['status'], unique=False)
    op.create_index(op.f('ix_runs_task_status'), 'runs', ['task_status'], unique=False)
    op.create_index(op.f('ix_runs_user_id'), 'runs', ['user_id'], unique=False)

    # ### Removed api_keys table - not needed in simple dev mode ###

    # ### Removed sessions table - agent runs are standalone now ###

    # ### Create agent_outputs table ###
    op.create_table('agent_outputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('variation_id', sa.Integer(), nullable=False),
        sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('output_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['runs.task_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_outputs_task_id'), 'agent_outputs', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_outputs_variation_id'), 'agent_outputs', ['variation_id'], unique=False)
    op.create_index(op.f('ix_agent_outputs_timestamp'), 'agent_outputs', ['timestamp'], unique=False)

    # ### Removed model_variants table - no LiteLLM functionality needed ###

    # ### Removed turns table - agent runs are standalone now ###

    # ### Removed preferences table - agent runs are standalone now ###


def downgrade() -> None:
    # ### Drop all tables in reverse order ###
    # No sessions, turns, or preferences tables to drop
    
    # No model_variants table to drop
    
    op.drop_index(op.f('ix_agent_outputs_timestamp'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_variation_id'), table_name='agent_outputs')
    op.drop_index(op.f('ix_agent_outputs_task_id'), table_name='agent_outputs')
    op.drop_table('agent_outputs')
    
    # No sessions table to drop
    
    # No api_keys table to drop
    
    op.drop_index(op.f('ix_runs_user_id'), table_name='runs')
    op.drop_index(op.f('ix_runs_task_status'), table_name='runs')
    op.drop_index(op.f('ix_runs_status'), table_name='runs')
    op.drop_index(op.f('ix_runs_run_id'), table_name='runs')
    op.drop_index(op.f('ix_runs_github_url'), table_name='runs')
    op.drop_index(op.f('ix_runs_created_at'), table_name='runs')
    op.drop_table('runs')
    op.execute("DROP SEQUENCE IF EXISTS runs_task_id_seq")
    
    # No provider_credentials table to drop
    
    # No model_definitions table to drop
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # No enum type to drop