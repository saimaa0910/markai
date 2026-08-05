"""add social to agenttype

Revision ID: 720e36f3966a
Revises: 39c8719ce9b6
Create Date: 2026-08-04 17:12:56.820060

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '720e36f3966a'
down_revision: Union[str, None] = '39c8719ce9b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Under SQLite (development DB), Enum columns are stored as TEXT/VARCHAR.
    # Therefore, no DDL modifications are needed for SQLite.
    # For Postgres/Production target, we would do op.execute("ALTER TYPE agenttype ADD VALUE 'SOCIAL'")
    pass


def downgrade() -> None:
    pass
