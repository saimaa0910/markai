"""Sprint 8.3.1 Phase 4 - Security Hardening

Revision ID: d3e4f5g6h7i8
Revises: c1d2e3f4g5h6
Create Date: 2026-05-21

**Phase 4 Deliverables**:
- Trusted device management
- MFA recovery codes
- Rate limiting infrastructure
- Advanced security features

Changes:
1. New table: trusted_devices
2. New table: mfa_recovery_codes
3. New table: rate_limit_log
4. users table: 3 new columns
   - mfa_recovery_codes_generated_at
   - trusted_devices_enabled
   - trust_device_duration_days
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'd3e4f5g6h7i8'
down_revision = 'c1d2e3f4g5h6'  # Phase 3 migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # 1. Update users table with Phase 4 fields
    # ========================================================================
    
    op.add_column(
        'users',
        sa.Column(
            'mfa_recovery_codes_generated_at',
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment='When MFA recovery codes were last generated',
        ),
    )
    
    op.add_column(
        'users',
        sa.Column(
            'trusted_devices_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='TRUE',
            comment='Whether user has device trust feature enabled',
        ),
    )
    
    op.add_column(
        'users',
        sa.Column(
            'trust_device_duration_days',
            sa.Integer(),
            nullable=True,
            server_default='30',
            comment='How many days a trusted device remains trusted',
        ),
    )
    
    # ========================================================================
    # 2. Create trusted_devices table
    # ========================================================================
    
    op.create_table(
        'trusted_devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_fingerprint', sa.Text(), nullable=False, comment='Unique device identifier'),
        sa.Column('device_name', sa.Text(), nullable=True, comment='User-friendly device name'),
        sa.Column('device_type', sa.String(50), nullable=True, comment='mobile, desktop, tablet'),
        sa.Column('browser', sa.String(100), nullable=True, comment='Browser name and version'),
        sa.Column('os', sa.String(100), nullable=True, comment='Operating system'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IP address when trusted'),
        sa.Column('location', sa.Text(), nullable=True, comment='Geo-location when trusted'),
        sa.Column('trusted_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='When device was trusted'),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='When trust expires (NULL = never)'),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='Last time this device was used'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE', comment='Whether trust is still active'),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='When trust was revoked'),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='User who revoked (for admin revocations)'),
        sa.Column('revoke_reason', sa.Text(), nullable=True, comment='Reason for revocation'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Indexes for trusted_devices
    op.create_index(
        'idx_trusted_devices_user_active',
        'trusted_devices',
        ['user_id', 'is_active'],
        comment='Fast lookup of user\'s active trusted devices',
    )
    
    op.create_index(
        'idx_trusted_devices_fingerprint',
        'trusted_devices',
        ['device_fingerprint'],
        comment='Fast device fingerprint lookup',
    )
    
    op.create_index(
        'idx_trusted_devices_expires',
        'trusted_devices',
        ['expires_at'],
        postgresql_where=sa.text('expires_at IS NOT NULL'),
        comment='Partial index for expiring devices (cleanup job)',
    )
    
    # ========================================================================
    # 3. Create mfa_recovery_codes table
    # ========================================================================
    
    op.create_table(
        'mfa_recovery_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code_hash', sa.Text(), nullable=False, comment='SHA-256 hash of recovery code'),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='FALSE', comment='Whether code has been used'),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='When code was used'),
        sa.Column('used_from_ip', sa.String(45), nullable=True, comment='IP address where code was used'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Indexes for mfa_recovery_codes
    op.create_index(
        'idx_mfa_recovery_codes_user',
        'mfa_recovery_codes',
        ['user_id'],
        comment='Fast lookup of user\'s recovery codes',
    )
    
    op.create_index(
        'idx_mfa_recovery_codes_active',
        'mfa_recovery_codes',
        ['user_id', 'is_used'],
        comment='Fast lookup of unused recovery codes',
    )
    
    # ========================================================================
    # 4. Create rate_limit_log table
    # ========================================================================
    
    op.create_table(
        'rate_limit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('endpoint', sa.String(255), nullable=False, comment='API endpoint that was rate limited'),
        sa.Column('ip_address', sa.String(45), nullable=False, comment='IP address of request'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='User ID if authenticated'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1', comment='Number of attempts in this window'),
        sa.Column('window_start', sa.TIMESTAMP(timezone=True), nullable=False, comment='Start of rate limit window'),
        sa.Column('window_end', sa.TIMESTAMP(timezone=True), nullable=False, comment='End of rate limit window'),
        sa.Column('blocked', sa.Boolean(), nullable=False, server_default='FALSE', comment='Whether request was blocked'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Indexes for rate_limit_log
    op.create_index(
        'idx_rate_limit_log_ip_endpoint',
        'rate_limit_log',
        ['ip_address', 'endpoint', 'window_end'],
        comment='Fast rate limit checks by IP and endpoint',
    )
    
    op.create_index(
        'idx_rate_limit_log_user',
        'rate_limit_log',
        ['user_id', 'created_at'],
        comment='User rate limit history',
    )


def downgrade() -> None:
    # Drop tables (reverse order)
    op.drop_table('rate_limit_log')
    op.drop_table('mfa_recovery_codes')
    op.drop_table('trusted_devices')
    
    # Drop users columns
    op.drop_column('users', 'trust_device_duration_days')
    op.drop_column('users', 'trusted_devices_enabled')
    op.drop_column('users', 'mfa_recovery_codes_generated_at')
