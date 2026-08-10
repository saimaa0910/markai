"""Sprint 8.3.1 Phase 3 - Account Lifecycle & Data Management

Revision ID: c1d2e3f4g5h6
Revises: b9c2d3e4f5a6
Create Date: 2026-05-21 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, None] = 'b9c2d3e4f5a6'  # Phase 2 migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add fields for advanced account lifecycle management:
    - Account deactivation tracking
    - Export history
    - Audit trail enhancements
    """
    
    # Add deactivation tracking to users table
    op.add_column('users', sa.Column('deactivated_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deactivation_reason', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_export_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('users', sa.Column('export_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Add indexes for common queries
    op.create_index(
        'idx_users_deactivated_at',
        'users',
        ['deactivated_at'],
        unique=False,
        postgresql_where=sa.text('deactivated_at IS NOT NULL')
    )
    
    # Index for finding accounts pending cleanup
    op.create_index(
        'idx_users_lifecycle_status',
        'users',
        ['is_active', 'is_locked', 'deleted_at'],
        unique=False
    )
    
    # Create account_audit_log table for comprehensive audit trail
    op.create_table(
        'account_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Indexes for audit log queries
    op.create_index('idx_audit_log_user_time', 'account_audit_log', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_audit_log_event_type', 'account_audit_log', ['event_type', 'created_at'], unique=False)
    op.create_index('idx_audit_log_performed_by', 'account_audit_log', ['performed_by', 'created_at'], unique=False)
    
    # Create data_export_history table to track GDPR exports
    op.create_table(
        'data_export_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('export_format', sa.String(20), nullable=False),  # json, csv
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='completed'),  # pending, completed, failed
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    
    # Index for export history queries
    op.create_index('idx_export_history_user_time', 'data_export_history', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """
    Revert Phase 3 changes.
    """
    # Drop tables
    op.drop_table('data_export_history')
    op.drop_table('account_audit_log')
    
    # Drop indexes
    op.drop_index('idx_users_lifecycle_status', table_name='users')
    op.drop_index('idx_users_deactivated_at', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'export_count')
    op.drop_column('users', 'last_export_at')
    op.drop_column('users', 'deactivation_reason')
    op.drop_column('users', 'deactivated_at')
