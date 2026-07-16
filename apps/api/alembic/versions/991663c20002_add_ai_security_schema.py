"""add_ai_security_schema

Revision ID: 991663c20002
Revises: fc54bf6b6c8f
Create Date: 2026-07-15 22:41:12.842940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '991663c20002'
down_revision: Union[str, None] = 'fc54bf6b6c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'ai_quota_usages' not in tables:
        op.create_table('ai_quota_usages',
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('daily_tokens', sa.Integer(), nullable=False),
        sa.Column('monthly_tokens', sa.Integer(), nullable=False),
        sa.Column('daily_requests', sa.Integer(), nullable=False),
        sa.Column('monthly_requests', sa.Integer(), nullable=False),
        sa.Column('daily_spend', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('monthly_spend', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('last_reset_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )

    if 'ai_scan_logs' not in tables:
        op.create_table('ai_scan_logs',
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('prompt_length', sa.Integer(), nullable=False),
        sa.Column('prompt_complexity', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('pii_detected', sa.Boolean(), nullable=False),
        sa.Column('secrets_detected', sa.Boolean(), nullable=False),
        sa.Column('injection_risk', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )

    if 'ai_security_events' not in tables:
        op.create_table('ai_security_events',
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('trigger_source', sa.String(length=20), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.String(length=20), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )

    if 'ai_security_policy_rules' not in tables:
        op.create_table('ai_security_policy_rules',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('allowed_providers', sa.JSON(), nullable=True),
        sa.Column('allowed_models', sa.JSON(), nullable=True),
        sa.Column('daily_token_limit', sa.Integer(), nullable=False),
        sa.Column('daily_request_limit', sa.Integer(), nullable=False),
        sa.Column('monthly_token_limit', sa.Integer(), nullable=False),
        sa.Column('monthly_request_limit', sa.Integer(), nullable=False),
        sa.Column('daily_budget_usd', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('monthly_budget_usd', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('moderation_actions', sa.JSON(), nullable=True),
        sa.Column('pii_masking_policy', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    op.drop_table('ai_security_policy_rules')
    op.drop_table('ai_security_events')
    op.drop_table('ai_scan_logs')
    op.drop_table('ai_quota_usages')
