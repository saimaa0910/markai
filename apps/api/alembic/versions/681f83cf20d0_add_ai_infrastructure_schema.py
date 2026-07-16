"""add_ai_infrastructure_schema

Revision ID: 681f83cf20d0
Revises: 19b13d08a3eb
Create Date: 2026-07-15 22:02:30.777726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '681f83cf20d0'
down_revision: Union[str, None] = '19b13d08a3eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'background_jobs' not in tables:
        op.create_table('background_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('args', sa.String(length=1000), nullable=True),
        sa.Column('kwargs', sa.String(length=1000), nullable=True),
        sa.Column('result', sa.String(length=4000), nullable=True),
        sa.Column('error', sa.String(length=4000), nullable=True),
        sa.Column('runtime', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_background_jobs_name'), 'background_jobs', ['name'], unique=False)
        op.create_index(op.f('ix_background_jobs_task_id'), 'background_jobs', ['task_id'], unique=False)
    
    if 'cache_metadata' not in tables:
        op.create_table('cache_metadata',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('namespace', sa.String(length=100), nullable=True),
        sa.Column('hits', sa.Integer(), nullable=True),
        sa.Column('misses', sa.Integer(), nullable=True),
        sa.Column('hit_ratio', sa.Float(), nullable=True),
        sa.Column('evictions', sa.Integer(), nullable=True),
        sa.Column('keys_count', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_cache_metadata_namespace'), 'cache_metadata', ['namespace'], unique=False)
    
    if 'job_history' not in tables:
        op.create_table('job_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=True),
        sa.Column('task_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.String(length=4000), nullable=True),
        sa.Column('triggered_by', sa.String(length=255), nullable=True),
        sa.Column('execution_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_job_history_job_id'), 'job_history', ['job_id'], unique=False)
        op.create_index(op.f('ix_job_history_task_name'), 'job_history', ['task_name'], unique=False)
    
    if 'queue_messages' not in tables:
        op.create_table('queue_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('queue_name', sa.String(length=100), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('processed_count', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_queue_messages_queue_name'), 'queue_messages', ['queue_name'], unique=False)
    
    if 'scheduler_history' not in tables:
        op.create_table('scheduler_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=True),
        sa.Column('schedule', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.String(length=4000), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_scheduler_history_task_name'), 'scheduler_history', ['task_name'], unique=False)
    
    if 'worker_metrics' not in tables:
        op.create_table('worker_metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('worker_name', sa.String(length=255), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('ram_used_mb', sa.Float(), nullable=True),
        sa.Column('ram_total_mb', sa.Float(), nullable=True),
        sa.Column('active_tasks_count', sa.Integer(), nullable=True),
        sa.Column('throughput', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_worker_metrics_worker_name'), 'worker_metrics', ['worker_name'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_worker_metrics_worker_name'), table_name='worker_metrics')
    op.drop_table('worker_metrics')
    op.drop_index(op.f('ix_scheduler_history_task_name'), table_name='scheduler_history')
    op.drop_table('scheduler_history')
    op.drop_index(op.f('ix_queue_messages_queue_name'), table_name='queue_messages')
    op.drop_table('queue_messages')
    op.drop_index(op.f('ix_job_history_task_name'), table_name='job_history')
    op.drop_index(op.f('ix_job_history_job_id'), table_name='job_history')
    op.drop_table('job_history')
    op.drop_index(op.f('ix_cache_metadata_namespace'), table_name='cache_metadata')
    op.drop_table('cache_metadata')
    op.drop_index(op.f('ix_background_jobs_task_id'), table_name='background_jobs')
    op.drop_index(op.f('ix_background_jobs_name'), table_name='background_jobs')
    op.drop_table('background_jobs')
    # ### end Alembic commands ###
