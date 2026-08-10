"""Sprint 8.3.1 Phase 2 - Session Management Enhancements

Revision ID: b9c2d3e4f5a6
Revises: a8b9c1d2e3f4
Create Date: 2026-05-21 14:00:00.000000

Enhances user_sessions table with:
- User-friendly device naming and identification
- Better location tracking and display
- Session activity metrics
- Device type classification
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b9c2d3e4f5a6'
down_revision = 'a8b9c1d2e3f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add session enhancement fields
    op.add_column('user_sessions', sa.Column('device_name', sa.String(255), nullable=True,
                                             comment='User-friendly device name (e.g. "My iPhone", "Work Laptop")'))
    op.add_column('user_sessions', sa.Column('device_type', sa.String(50), nullable=True,
                                             comment='Device category: mobile, tablet, desktop, bot, unknown'))
    op.add_column('user_sessions', sa.Column('browser', sa.String(100), nullable=True,
                                             comment='Browser name (Chrome, Safari, Firefox, etc.)'))
    op.add_column('user_sessions', sa.Column('browser_version', sa.String(50), nullable=True,
                                             comment='Browser version'))
    op.add_column('user_sessions', sa.Column('os', sa.String(100), nullable=True,
                                             comment='Operating system (Windows, macOS, iOS, Android, etc.)'))
    op.add_column('user_sessions', sa.Column('os_version', sa.String(50), nullable=True,
                                             comment='OS version'))
    op.add_column('user_sessions', sa.Column('location', sa.String(255), nullable=True,
                                             comment='Formatted location string (e.g. "San Francisco, US")'))
    op.add_column('user_sessions', sa.Column('region', sa.String(100), nullable=True,
                                             comment='State/region name'))
    op.add_column('user_sessions', sa.Column('latitude', sa.Float, nullable=True,
                                             comment='Approximate latitude for geo anomaly detection'))
    op.add_column('user_sessions', sa.Column('longitude', sa.Float, nullable=True,
                                             comment='Approximate longitude for geo anomaly detection'))
    op.add_column('user_sessions', sa.Column('request_count', sa.Integer, nullable=False, server_default='0',
                                             comment='Total API requests made in this session'))
    op.add_column('user_sessions', sa.Column('last_request_at', sa.DateTime(timezone=True), nullable=True,
                                             comment='Timestamp of last API request (more granular than last_activity_at)'))
    op.add_column('user_sessions', sa.Column('is_suspicious', sa.Boolean, nullable=False, server_default='FALSE',
                                             comment='Flagged for suspicious activity (geo anomaly, unusual behavior, etc.)'))
    op.add_column('user_sessions', sa.Column('suspicious_flags', postgresql.JSONB, nullable=True,
                                             comment='Array of suspicious activity reasons'))
    
    # Add indexes for new query patterns
    op.create_index('idx_user_sessions_device_type', 'user_sessions', ['device_type'])
    op.create_index('idx_user_sessions_suspicious', 'user_sessions', ['user_id', 'is_suspicious'],
                   postgresql_where='is_suspicious = TRUE')
    op.create_index('idx_user_sessions_location', 'user_sessions', ['country_code', 'city'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_sessions_location', table_name='user_sessions')
    op.drop_index('idx_user_sessions_suspicious', table_name='user_sessions')
    op.drop_index('idx_user_sessions_device_type', table_name='user_sessions')
    
    # Drop columns
    op.drop_column('user_sessions', 'suspicious_flags')
    op.drop_column('user_sessions', 'is_suspicious')
    op.drop_column('user_sessions', 'last_request_at')
    op.drop_column('user_sessions', 'request_count')
    op.drop_column('user_sessions', 'longitude')
    op.drop_column('user_sessions', 'latitude')
    op.drop_column('user_sessions', 'region')
    op.drop_column('user_sessions', 'location')
    op.drop_column('user_sessions', 'os_version')
    op.drop_column('user_sessions', 'os')
    op.drop_column('user_sessions', 'browser_version')
    op.drop_column('user_sessions', 'browser')
    op.drop_column('user_sessions', 'device_type')
    op.drop_column('user_sessions', 'device_name')
