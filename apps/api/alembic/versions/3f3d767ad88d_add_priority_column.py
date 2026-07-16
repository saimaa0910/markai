"""add priority column

Revision ID: 3f3d767ad88d
Revises: 991663c20002
Create Date: 2026-07-16 10:06:16.864255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f3d767ad88d'
down_revision: Union[str, None] = '991663c20002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_security_policy_rules', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('ai_security_policy_rules', 'priority')
