"""add_invitations_and_verification

Revision ID: b31a73462d04
Revises: b2c3d4e5f6a1
Create Date: 2026-07-15 10:16:20.046109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b31a73462d04'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create organization_invitations table
    op.create_table('organization_invitations',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'GUEST', name='userrole'), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('is_accepted', sa.Boolean(), nullable=False),
        sa.Column('is_rejected', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_invitations_email'), 'organization_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_organization_invitations_token'), 'organization_invitations', ['token'], unique=True)
    
    # 2. Add is_verified and preferences columns to users
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'is_verified')
    op.drop_index(op.f('ix_organization_invitations_token'), table_name='organization_invitations')
    op.drop_index(op.f('ix_organization_invitations_email'), table_name='organization_invitations')
    op.drop_table('organization_invitations')
