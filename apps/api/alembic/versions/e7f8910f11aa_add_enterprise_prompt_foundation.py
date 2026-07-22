"""add_enterprise_prompt_foundation

Revision ID: e7f8910f11aa
Revises: c8f9021a3b4e
Create Date: 2026-07-21 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7f8910f11aa'
down_revision: Union[str, None] = 'c8f9021a3b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. prompt_categories
    op.create_table(
        'prompt_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'organization_id', name='uq_prompt_category_name_org')
    )
    op.create_index(op.f('ix_prompt_categories_name'), 'prompt_categories', ['name'], unique=False)
    op.create_index(op.f('ix_prompt_categories_organization_id'), 'prompt_categories', ['organization_id'], unique=False)

    # 2. prompt_tags
    op.create_table(
        'prompt_tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'organization_id', name='uq_prompt_tag_name_org')
    )
    op.create_index(op.f('ix_prompt_tags_name'), 'prompt_tags', ['name'], unique=False)
    op.create_index(op.f('ix_prompt_tags_organization_id'), 'prompt_tags', ['organization_id'], unique=False)

    # 3. Add columns to prompts if not exists
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('category_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('prompt_type', sa.String(length=50), server_default='text', nullable=False))
        batch_op.create_foreign_key('fk_prompts_category_id', 'prompt_categories', ['category_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_prompts_category_id'), ['category_id'], unique=False)

    # 4. prompt_tags_association
    op.create_table(
        'prompt_tags_association',
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['prompt_tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('prompt_id', 'tag_id')
    )

    # 5. prompt_variables
    op.create_table(
        'prompt_variables',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('version_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('variable_type', sa.String(length=50), server_default='string', nullable=False),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['prompt_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompt_variables_name'), 'prompt_variables', ['name'], unique=False)
    op.create_index(op.f('ix_prompt_variables_organization_id'), 'prompt_variables', ['organization_id'], unique=False)
    op.create_index(op.f('ix_prompt_variables_prompt_id'), 'prompt_variables', ['prompt_id'], unique=False)

    # 6. prompt_shares
    op.create_table(
        'prompt_shares',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('share_token', sa.String(length=255), nullable=False),
        sa.Column('visibility', sa.String(length=50), server_default='organization', nullable=False),
        sa.Column('is_editable', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shared_by', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token')
    )
    op.create_index(op.f('ix_prompt_shares_organization_id'), 'prompt_shares', ['organization_id'], unique=False)
    op.create_index(op.f('ix_prompt_shares_prompt_id'), 'prompt_shares', ['prompt_id'], unique=False)

    # 7. prompt_favorites
    op.create_table(
        'prompt_favorites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id', 'user_id', 'organization_id', name='uq_prompt_fav_user_org')
    )
    op.create_index(op.f('ix_prompt_favorites_organization_id'), 'prompt_favorites', ['organization_id'], unique=False)
    op.create_index(op.f('ix_prompt_favorites_prompt_id'), 'prompt_favorites', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_prompt_favorites_user_id'), 'prompt_favorites', ['user_id'], unique=False)

    # 8. prompt_analytics
    op.create_table(
        'prompt_analytics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('total_executions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_cost_usd', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_latency_ms', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('success_rate', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id')
    )
    op.create_index(op.f('ix_prompt_analytics_organization_id'), 'prompt_analytics', ['organization_id'], unique=False)
    op.create_index(op.f('ix_prompt_analytics_prompt_id'), 'prompt_analytics', ['prompt_id'], unique=False)

    # 9. prompt_templates
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), server_default='General', nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('variable_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('is_system_preset', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompt_templates_category'), 'prompt_templates', ['category'], unique=False)
    op.create_index(op.f('ix_prompt_templates_name'), 'prompt_templates', ['name'], unique=False)

    # 10. prompt_audit_logs
    op.create_table(
        'prompt_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=True),
        sa.Column('prompt_name', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompt_audit_logs_action'), 'prompt_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_prompt_audit_logs_organization_id'), 'prompt_audit_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_prompt_audit_logs_prompt_id'), 'prompt_audit_logs', ['prompt_id'], unique=False)
    op.create_index(op.f('ix_prompt_audit_logs_user_id'), 'prompt_audit_logs', ['user_id'], unique=False)

    # 11. Add system_prompt to prompt_versions if missing
    with op.batch_alter_table('prompt_versions') as batch_op:
        batch_op.add_column(sa.Column('system_prompt', sa.Text(), nullable=True))

    # 12. Add owner_id to prompt_collections & prompt_folders if missing
    with op.batch_alter_table('prompt_collections') as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_prompt_collections_owner_id', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('prompt_folders') as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_prompt_folders_owner_id', 'users', ['owner_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_table('prompt_audit_logs')
    op.drop_table('prompt_templates')
    op.drop_table('prompt_analytics')
    op.drop_table('prompt_favorites')
    op.drop_table('prompt_shares')
    op.drop_table('prompt_variables')
    op.drop_table('prompt_tags_association')
    
    with op.batch_alter_table('prompts') as batch_op:
        batch_op.drop_constraint('fk_prompts_category_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_prompts_category_id'))
        batch_op.drop_column('prompt_type')
        batch_op.drop_column('category_id')
        batch_op.drop_column('description')

    with op.batch_alter_table('prompt_versions') as batch_op:
        batch_op.drop_column('system_prompt')

    with op.batch_alter_table('prompt_collections') as batch_op:
        batch_op.drop_constraint('fk_prompt_collections_owner_id', type_='foreignkey')
        batch_op.drop_column('owner_id')

    with op.batch_alter_table('prompt_folders') as batch_op:
        batch_op.drop_constraint('fk_prompt_folders_owner_id', type_='foreignkey')
        batch_op.drop_column('owner_id')

    op.drop_table('prompt_tags')
    op.drop_table('prompt_categories')
