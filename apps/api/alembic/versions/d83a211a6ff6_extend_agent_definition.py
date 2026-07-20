"""extend_agent_definition

Revision ID: d83a211a6ff6
Revises: 162bd0003e72
Create Date: 2026-07-17 17:22:56.224476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd83a211a6ff6'
down_revision: Union[str, None] = '162bd0003e72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agent_definitions', sa.Column('preferred_provider', sa.String(length=100), nullable=True))
    op.add_column('agent_definitions', sa.Column('top_p', sa.Float(), nullable=True))
    op.add_column('agent_definitions', sa.Column('reasoning_mode', sa.String(length=50), nullable=True))
    op.add_column('agent_definitions', sa.Column('execution_mode', sa.String(length=50), nullable=True))
    op.add_column('agent_definitions', sa.Column('avatar', sa.String(length=500), nullable=True))
    op.add_column('agent_definitions', sa.Column('avatar_color', sa.String(length=100), nullable=True))
    op.add_column('agent_definitions', sa.Column('welcome_message', sa.Text(), nullable=True))
    op.add_column('agent_definitions', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('agent_definitions', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('agent_definitions', 'is_pinned')
    op.drop_column('agent_definitions', 'is_favorite')
    op.drop_column('agent_definitions', 'welcome_message')
    op.drop_column('agent_definitions', 'avatar_color')
    op.drop_column('agent_definitions', 'avatar')
    op.drop_column('agent_definitions', 'execution_mode')
    op.drop_column('agent_definitions', 'reasoning_mode')
    op.drop_column('agent_definitions', 'top_p')
    op.drop_column('agent_definitions', 'preferred_provider')
