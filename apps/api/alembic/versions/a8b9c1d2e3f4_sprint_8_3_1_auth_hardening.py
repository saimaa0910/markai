"""Sprint 8.3.1 Phase 1 - Authentication Hardening

Revision ID: a8b9c1d2e3f4
Revises: 532d3ff86c7a
Create Date: 2026-05-21 13:00:00.000000

Adds columns to the users table:
- is_locked
- failed_login_attempts
- change_password_required
- temporary_password
- temporary_password_expires_at
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a8b9c1d2e3f4'
down_revision = '532d3ff86c7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add authentication hardening fields to users table
    op.add_column(
        'users',
        sa.Column(
            'is_locked',
            sa.Boolean(),
            nullable=False,
            server_default='FALSE',
            comment='Whether the account is locked',
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'failed_login_attempts',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of failed login attempts since last success',
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'change_password_required',
            sa.Boolean(),
            nullable=False,
            server_default='FALSE',
            comment='Whether user must change their password on next login',
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'temporary_password',
            sa.String(255),
            nullable=True,
            comment='Encrypted temporary password for first login',
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'temporary_password_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Expiry time for temporary password',
        ),
    )


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'temporary_password_expires_at')
    op.drop_column('users', 'temporary_password')
    op.drop_column('users', 'change_password_required')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'is_locked')
