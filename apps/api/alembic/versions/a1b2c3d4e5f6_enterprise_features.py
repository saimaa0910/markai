"""enterprise_features_agents_memory_workflow_integrations

Revision ID: a1b2c3d4e5f6
Revises: 2e87819f588c
Create Date: 2026-07-14 08:00:00.000000

This migration:
1. Adds missing indexes on FK columns across all existing tables
2. Adds missing constraints (unique on user_organizations, prompts)
3. Makes Message.model_used nullable (fix)
4. Creates AI Agent Platform tables (agent_definitions, agent_sessions, agent_runs, agent_logs)
5. Creates Agent Memory tables (agent_memories, conversation_memories, organization_memories)
6. Creates Workflow Engine tables (workflow_definitions, workflow_executions, workflow_steps)
7. Creates Integration Platform tables (integrations, integration_credentials, sync_jobs)
8. Creates Notification Platform tables (notifications, notification_preferences)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2e87819f588c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. Missing indexes on existing tables ─────────────────────────────────

    # ai_token_usages hot path indexes
    op.create_index('ix_ai_token_usages_organization_id', 'ai_token_usages', ['organization_id'])
    op.create_index('ix_ai_token_usages_user_id', 'ai_token_usages', ['user_id'])
    op.create_index('ix_ai_token_usages_created_at', 'ai_token_usages', ['created_at'])

    # messages hot path indexes
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # document_chunks hot path indexes
    op.create_index('ix_document_chunks_organization_id', 'document_chunks', ['organization_id'])
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])

    # prompts composite index for frequent queries
    op.create_index('ix_prompts_org_id_name', 'prompts', ['organization_id', 'name'])

    # campaigns index
    op.create_index('ix_campaigns_organization_id', 'campaigns', ['organization_id'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])

    # CRM indexes
    op.create_index('ix_contacts_organization_id', 'contacts', ['organization_id'])
    op.create_index('ix_companies_organization_id', 'companies', ['organization_id'])
    op.create_index('ix_leads_organization_id', 'leads', ['organization_id'])

    # user_organizations unique constraint (prevent duplicate memberships)
    try:
        op.create_unique_constraint(
            'uq_user_organizations_user_org',
            'user_organizations',
            ['user_id', 'organization_id']
        )
    except Exception:
        pass  # Constraint may already exist

    # ─── 2. Fix Message.model_used nullable ────────────────────────────────────
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('model_used', nullable=True)

    # ─── 3. Agent Platform Tables ──────────────────────────────────────────────

    op.create_table(
        'agent_definitions',
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agent_type', sa.String(50), nullable=False, server_default='CUSTOM'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('prompt_template_name', sa.String(255), nullable=True),
        sa.Column('allowed_tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_model', sa.String(100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('memory_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_memory_items', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_definitions_org_id', 'agent_definitions', ['organization_id'])
    op.create_index('ix_agent_definitions_type', 'agent_definitions', ['agent_type'])

    op.create_table(
        'agent_sessions',
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_sessions_org_id', 'agent_sessions', ['organization_id'])
    op.create_index('ix_agent_sessions_agent_id', 'agent_sessions', ['agent_id'])
    op.create_index('ix_agent_sessions_user_id', 'agent_sessions', ['user_id'])

    op.create_table(
        'agent_runs',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('agent_output', sa.Text(), nullable=True),
        sa.Column('plan', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_calls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('iterations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_runs_session_id', 'agent_runs', ['session_id'])
    op.create_index('ix_agent_runs_organization_id', 'agent_runs', ['organization_id'])
    op.create_index('ix_agent_runs_status', 'agent_runs', ['status'])

    op.create_table(
        'agent_logs',
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('level', sa.String(20), nullable=False, server_default='INFO'),
        sa.Column('step_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_logs_run_id', 'agent_logs', ['run_id'])

    # ─── 4. Memory Tables ──────────────────────────────────────────────────────

    op.create_table(
        'agent_memories',
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False, server_default='SHORT_TERM'),
        sa.Column('memory_key', sa.String(255), nullable=False),
        sa.Column('memory_value', sa.Text(), nullable=False),
        sa.Column('importance', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_memories_agent_id', 'agent_memories', ['agent_id'])
    op.create_index('ix_agent_memories_session_id', 'agent_memories', ['session_id'])
    op.create_index('ix_agent_memories_org_id', 'agent_memories', ['organization_id'])
    op.create_index('ix_agent_memories_memory_type', 'agent_memories', ['memory_type'])

    op.create_table(
        'conversation_memories',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('turns_covered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary_turn_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversation_memories_session_id', 'conversation_memories', ['session_id'])

    op.create_table(
        'organization_memories',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_organization_memories_org_id', 'organization_memories', ['organization_id'])
    op.create_index('ix_organization_memories_category', 'organization_memories', ['category'])

    # ─── 5. Workflow Tables ────────────────────────────────────────────────────

    op.create_table(
        'workflow_definitions',
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('trigger', sa.String(50), nullable=False, server_default='MANUAL'),
        sa.Column('steps_definition', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('webhook_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflow_definitions_org_id', 'workflow_definitions', ['organization_id'])
    op.create_index('ix_workflow_definitions_status', 'workflow_definitions', ['status'])

    op.create_table(
        'workflow_executions',
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('triggered_by', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
    op.create_index('ix_workflow_executions_org_id', 'workflow_executions', ['organization_id'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])

    op.create_table(
        'workflow_steps',
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('step_id', sa.String(100), nullable=False),
        sa.Column('step_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflow_steps_execution_id', 'workflow_steps', ['execution_id'])

    # ─── 6. Integration Tables ─────────────────────────────────────────────────

    op.create_table(
        'integrations',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING_AUTH'),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced_at', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_integrations_org_id', 'integrations', ['organization_id'])
    op.create_index('ix_integrations_provider', 'integrations', ['provider'])

    op.create_table(
        'integration_credentials',
        sa.Column('integration_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.String(50), nullable=True),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('extra', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('integration_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_integration_credentials_integration_id', 'integration_credentials', ['integration_id'])

    op.create_table(
        'sync_jobs',
        sa.Column('integration_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('records_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sync_jobs_integration_id', 'sync_jobs', ['integration_id'])
    op.create_index('ix_sync_jobs_org_id', 'sync_jobs', ['organization_id'])

    # ─── 7. Notification Tables ────────────────────────────────────────────────

    op.create_table(
        'notifications',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='IN_APP'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='MEDIUM'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('event_type', sa.String(100), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_org_id', 'notifications', ['organization_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    op.create_table(
        'notification_preferences',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('muted_event_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_prefs_user_id', 'notification_preferences', ['user_id'])


def downgrade() -> None:
    # Notifications
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    # Integrations
    op.drop_table('sync_jobs')
    op.drop_table('integration_credentials')
    op.drop_table('integrations')
    # Workflow
    op.drop_table('workflow_steps')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_definitions')
    # Memory
    op.drop_table('organization_memories')
    op.drop_table('conversation_memories')
    op.drop_table('agent_memories')
    # Agents
    op.drop_table('agent_logs')
    op.drop_table('agent_runs')
    op.drop_table('agent_sessions')
    op.drop_table('agent_definitions')
    # Revert model_used
    op.alter_column('messages', 'model_used', nullable=False)
    # Drop added indexes
    op.drop_index('ix_notification_prefs_user_id', 'notification_preferences')
    op.drop_index('ix_notifications_is_read', 'notifications')
    op.drop_index('ix_notifications_org_id', 'notifications')
    op.drop_index('ix_notifications_user_id', 'notifications')
    op.drop_index('ix_sync_jobs_org_id', 'sync_jobs')
    op.drop_index('ix_sync_jobs_integration_id', 'sync_jobs')
    op.drop_index('ix_integration_credentials_integration_id', 'integration_credentials')
    op.drop_index('ix_integrations_provider', 'integrations')
    op.drop_index('ix_integrations_org_id', 'integrations')
    op.drop_index('ix_workflow_steps_execution_id', 'workflow_steps')
    op.drop_index('ix_workflow_executions_status', 'workflow_executions')
    op.drop_index('ix_workflow_executions_org_id', 'workflow_executions')
    op.drop_index('ix_workflow_executions_workflow_id', 'workflow_executions')
    op.drop_index('ix_workflow_definitions_status', 'workflow_definitions')
    op.drop_index('ix_workflow_definitions_org_id', 'workflow_definitions')
    op.drop_index('ix_organization_memories_category', 'organization_memories')
    op.drop_index('ix_organization_memories_org_id', 'organization_memories')
    op.drop_index('ix_conversation_memories_session_id', 'conversation_memories')
    op.drop_index('ix_agent_memories_memory_type', 'agent_memories')
    op.drop_index('ix_agent_memories_org_id', 'agent_memories')
    op.drop_index('ix_agent_memories_session_id', 'agent_memories')
    op.drop_index('ix_agent_memories_agent_id', 'agent_memories')
    op.drop_index('ix_agent_logs_run_id', 'agent_logs')
    op.drop_index('ix_agent_runs_status', 'agent_runs')
    op.drop_index('ix_agent_runs_organization_id', 'agent_runs')
    op.drop_index('ix_agent_runs_session_id', 'agent_runs')
    op.drop_index('ix_agent_sessions_user_id', 'agent_sessions')
    op.drop_index('ix_agent_sessions_agent_id', 'agent_sessions')
    op.drop_index('ix_agent_sessions_org_id', 'agent_sessions')
    op.drop_index('ix_agent_definitions_type', 'agent_definitions')
    op.drop_index('ix_agent_definitions_org_id', 'agent_definitions')
    # Drop indexes on existing tables
    try:
        op.drop_constraint('uq_user_organizations_user_org', 'user_organizations')
    except Exception:
        pass
    op.drop_index('ix_leads_organization_id', 'leads')
    op.drop_index('ix_companies_organization_id', 'companies')
    op.drop_index('ix_contacts_organization_id', 'contacts')
    op.drop_index('ix_campaigns_status', 'campaigns')
    op.drop_index('ix_campaigns_organization_id', 'campaigns')
    op.drop_index('ix_prompts_org_id_name', 'prompts')
    op.drop_index('ix_document_chunks_document_id', 'document_chunks')
    op.drop_index('ix_document_chunks_organization_id', 'document_chunks')
    op.drop_index('ix_messages_conversation_id', 'messages')
    op.drop_index('ix_ai_token_usages_created_at', 'ai_token_usages')
    op.drop_index('ix_ai_token_usages_user_id', 'ai_token_usages')
    op.drop_index('ix_ai_token_usages_organization_id', 'ai_token_usages')
