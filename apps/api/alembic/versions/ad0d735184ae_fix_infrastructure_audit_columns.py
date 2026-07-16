"""fix_infrastructure_audit_columns

Revision ID: ad0d735184ae
Revises: c15511564b6b
Create Date: 2026-07-16 11:56:26.415705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad0d735184ae'
down_revision: Union[str, None] = 'c15511564b6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables that need: updated_at, created_by, updated_by, deleted_at
    tables_need_audit = ["background_jobs"]
    
    # Tables that need: created_at, updated_at, created_by, updated_by, deleted_at
    tables_need_all = [
        "job_history",
        "cache_metadata",
        "queue_messages",
        "scheduler_history",
        "worker_metrics",
        "ai_failover_events",
        "ai_quota_usages",
        "ai_routing_logs",
        "ai_routing_policies",
        "ai_scan_logs",
        "ai_security_events",
        "ai_security_policy_rules"
    ]

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def add_column_if_not_exists(table_name, col_name, col_type, **kwargs):
        # Verify table exists first
        if not inspector.has_table(table_name):
            return
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if col_name not in columns:
            op.add_column(table_name, sa.Column(col_name, col_type, **kwargs))

    # Add audit columns
    for table in tables_need_audit:
        add_column_if_not_exists(table, 'updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
        add_column_if_not_exists(table, 'created_by', sa.String(), nullable=True)
        add_column_if_not_exists(table, 'updated_by', sa.String(), nullable=True)
        add_column_if_not_exists(table, 'deleted_at', sa.DateTime(timezone=True), nullable=True)

    # Add created_at and audit columns
    for table in tables_need_all:
        add_column_if_not_exists(table, 'created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
        add_column_if_not_exists(table, 'updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
        add_column_if_not_exists(table, 'created_by', sa.String(), nullable=True)
        add_column_if_not_exists(table, 'updated_by', sa.String(), nullable=True)
        add_column_if_not_exists(table, 'deleted_at', sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    # Tables that need: updated_at, created_by, updated_by, deleted_at
    tables_need_audit = ["background_jobs"]
    
    # Tables that need: created_at, updated_at, created_by, updated_by, deleted_at
    tables_need_all = [
        "job_history",
        "cache_metadata",
        "queue_messages",
        "scheduler_history",
        "worker_metrics",
        "ai_failover_events",
        "ai_quota_usages",
        "ai_routing_logs",
        "ai_routing_policies",
        "ai_scan_logs",
        "ai_security_events",
        "ai_security_policy_rules"
    ]

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def drop_column_if_exists(table_name, col_name):
        if not inspector.has_table(table_name):
            return
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if col_name in columns:
            op.drop_column(table_name, col_name)

    for table in tables_need_audit:
        drop_column_if_exists(table, 'updated_at')
        drop_column_if_exists(table, 'created_by')
        drop_column_if_exists(table, 'updated_by')
        drop_column_if_exists(table, 'deleted_at')

    for table in tables_need_all:
        drop_column_if_exists(table, 'created_at')
        drop_column_if_exists(table, 'updated_at')
        drop_column_if_exists(table, 'created_by')
        drop_column_if_exists(table, 'updated_by')
        drop_column_if_exists(table, 'deleted_at')
