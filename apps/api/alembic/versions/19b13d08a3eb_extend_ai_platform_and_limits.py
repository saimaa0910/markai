"""extend_ai_platform_and_limits

Revision ID: 19b13d08a3eb
Revises: d64fb42be2ec
Create Date: 2026-07-15 21:21:25.843976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19b13d08a3eb'
down_revision: Union[str, None] = 'd64fb42be2ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the ai_org_limits table
    op.create_table('ai_org_limits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('credit_limit', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('credit_used', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('rpm_limit', sa.Integer(), nullable=False),
        sa.Column('tpm_limit', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id')
    )
    # Add new columns to ai_providers
    op.add_column('ai_providers', sa.Column('base_url', sa.String(length=255), nullable=True))
    op.add_column('ai_providers', sa.Column('api_version', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_providers', 'api_version')
    op.drop_column('ai_providers', 'base_url')
    op.drop_table('ai_org_limits')
