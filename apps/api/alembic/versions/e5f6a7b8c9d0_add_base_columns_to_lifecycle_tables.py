"""Add missing Base columns to account lifecycle tables

Revision ID: e5f6a7b8c9d0
Revises: d3e4f5g6h7i8
Create Date: 2026-08-18

Brings account_audit_log and data_export_history in line with the enterprise
Base contract (id, created_at, updated_at, deleted_at, created_by, updated_by,
version) so every table carries the standard audit/soft-delete/lock columns.
Columns are added as nullable / defaulted so existing databases upgrade in place.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'e5f6a7b8c9d0'
down_revision = 'd3e4f5g6h7i8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # account_audit_log
    op.add_column('account_audit_log', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('account_audit_log', sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('account_audit_log', sa.Column('created_by', sa.String(), nullable=True))
    op.add_column('account_audit_log', sa.Column('updated_by', sa.String(), nullable=True))
    op.add_column('account_audit_log', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    # data_export_history
    op.add_column('data_export_history', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('data_export_history', sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('data_export_history', sa.Column('created_by', sa.String(), nullable=True))
    op.add_column('data_export_history', sa.Column('updated_by', sa.String(), nullable=True))
    op.add_column('data_export_history', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    for table in ('data_export_history', 'account_audit_log'):
        op.drop_column(table, 'version')
        op.drop_column(table, 'updated_by')
        op.drop_column(table, 'created_by')
        op.drop_column(table, 'deleted_at')
        op.drop_column(table, 'updated_at')
