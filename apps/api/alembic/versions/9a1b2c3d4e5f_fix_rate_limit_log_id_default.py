"""Fix rate_limit_log id default

Revision ID: 9a1b2c3d4e5f
Revises: e5f6a7b8c9d0
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9a1b2c3d4e5f'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('rate_limit_log', 'id',
        server_default=sa.text('gen_random_uuid()'),
        existing_type=postgresql.UUID()
    )


def downgrade() -> None:
    op.alter_column('rate_limit_log', 'id',
        server_default=None,
        existing_type=postgresql.UUID()
    )