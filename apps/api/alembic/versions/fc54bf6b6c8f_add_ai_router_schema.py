"""add_ai_router_schema

Revision ID: fc54bf6b6c8f
Revises: 681f83cf20d0
Create Date: 2026-07-15 22:24:24.555185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc54bf6b6c8f'
down_revision: Union[str, None] = '681f83cf20d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'ai_failover_events' not in tables:
        op.create_table('ai_failover_events',
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('failed_provider', sa.String(length=50), nullable=False),
        sa.Column('failed_model', sa.String(length=100), nullable=False),
        sa.Column('fallback_provider', sa.String(length=50), nullable=False),
        sa.Column('fallback_model', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_attempts', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )

    if 'ai_routing_logs' not in tables:
        op.create_table('ai_routing_logs',
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('strategy_used', sa.String(length=50), nullable=False),
        sa.Column('selected_provider', sa.String(length=50), nullable=False),
        sa.Column('selected_model', sa.String(length=100), nullable=False),
        sa.Column('fallback_count', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )

    if 'ai_routing_policies' not in tables:
        op.create_table('ai_routing_policies',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('scope_id', sa.String(length=100), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('routing_strategy', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('ai_routing_policies')
    op.drop_table('ai_routing_logs')
    op.drop_table('ai_failover_events')
