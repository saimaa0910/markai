"""add_prompt_platform_phase2

Revision ID: b7e8910f45a2
Revises: d83a211a6ff6
Create Date: 2026-07-21 10:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7e8910f45a2'
down_revision: Union[str, None] = 'd83a211a6ff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. prompt_collections
    op.create_table(
        'prompt_collections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('visibility', sa.String(length=50), nullable=False, server_default='ORGANIZATION'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['prompt_collections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_collections_org_id', 'prompt_collections', ['organization_id'])

    # 2. prompt_folders
    op.create_table(
        'prompt_folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['prompt_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['prompt_folders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_folders_org_id', 'prompt_folders', ['organization_id'])
    op.create_index('ix_prompt_folders_collection_id', 'prompt_folders', ['collection_id'])

    # 3. Add extended columns to prompts
    op.add_column('prompts', sa.Column('folder_id', sa.UUID(), nullable=True))
    op.add_column('prompts', sa.Column('collection_id', sa.UUID(), nullable=True))
    op.add_column('prompts', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('prompts', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('prompts', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('prompts', sa.Column('status', sa.String(length=50), nullable=False, server_default='approved'))
    op.add_column('prompts', sa.Column('change_log', sa.Text(), nullable=True))
    op.add_column('prompts', sa.Column('owner_id', sa.UUID(), nullable=True))
    op.add_column('prompts', sa.Column('variable_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('prompts', sa.Column('visibility', sa.String(length=50), nullable=False, server_default='organization'))
    op.add_column('prompts', sa.Column('share_token', sa.String(length=255), nullable=True))
    op.add_column('prompts', sa.Column('share_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('prompts', sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='true'))

    op.create_foreign_key('fk_prompts_folder_id', 'prompts', 'prompt_folders', ['folder_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_prompts_collection_id', 'prompts', 'prompt_collections', ['collection_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_prompts_owner_id', 'prompts', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_prompts_share_token', 'prompts', ['share_token'])

    # 4. prompt_comments
    op.create_table(
        'prompt_comments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. prompt_test_cases
    op.create_table(
        'prompt_test_cases',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('inputs', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('expected_output', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. prompt_evaluations
    op.create_table(
        'prompt_evaluations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('test_case_id', sa.UUID(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('actual_output', sa.Text(), nullable=True),
        sa.Column('correctness_score', sa.Float(), nullable=True),
        sa.Column('grounding_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('safety_score', sa.Float(), nullable=True),
        sa.Column('hallucination_risk', sa.Float(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pass'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_case_id'], ['prompt_test_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. prompt_executions
    op.create_table(
        'prompt_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=True),
        sa.Column('prompt_name', sa.String(length=255), nullable=False),
        sa.Column('prompt_version', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('variables_used', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('user_prompt', sa.Text(), nullable=False),
        sa.Column('output', sa.Text(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_executions_org_id', 'prompt_executions', ['organization_id'])
    op.create_index('ix_prompt_executions_user_id', 'prompt_executions', ['user_id'])


def downgrade() -> None:
    op.drop_table('prompt_executions')
    op.drop_table('prompt_evaluations')
    op.drop_table('prompt_test_cases')
    op.drop_table('prompt_comments')
    
    op.drop_index('ix_prompts_share_token', 'prompts')
    op.drop_constraint('fk_prompts_owner_id', 'prompts', type_='foreignkey')
    op.drop_constraint('fk_prompts_collection_id', 'prompts', type_='foreignkey')
    op.drop_constraint('fk_prompts_folder_id', 'prompts', type_='foreignkey')

    op.drop_column('prompts', 'is_editable')
    op.drop_column('prompts', 'share_expires_at')
    op.drop_column('prompts', 'share_token')
    op.drop_column('prompts', 'visibility')
    op.drop_column('prompts', 'variable_specs')
    op.drop_column('prompts', 'owner_id')
    op.drop_column('prompts', 'change_log')
    op.drop_column('prompts', 'status')
    op.drop_column('prompts', 'is_pinned')
    op.drop_column('prompts', 'is_favorite')
    op.drop_column('prompts', 'is_archived')
    op.drop_column('prompts', 'collection_id')
    op.drop_column('prompts', 'folder_id')

    op.drop_table('prompt_folders')
    op.drop_table('prompt_collections')
