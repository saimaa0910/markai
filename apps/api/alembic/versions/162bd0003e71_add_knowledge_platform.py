"""add_knowledge_platform

Revision ID: 162bd0003e71
Revises: 97fb70bc43b2
Create Date: 2026-07-17 06:24:20.842809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '162bd0003e71'
down_revision: Union[str, None] = '97fb70bc43b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create collections table
    op.create_table(
        'knowledge_collections',
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
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['knowledge_collections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create folders table
    op.create_table(
        'knowledge_folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['knowledge_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['knowledge_folders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Add columns to knowledge_documents
    op.add_column('knowledge_documents', sa.Column('collection_id', sa.UUID(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('folder_id', sa.UUID(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('storage_url', sa.Text(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('knowledge_documents', sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('knowledge_documents', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('knowledge_documents', sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column('knowledge_documents', sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('knowledge_documents', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('knowledge_documents', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('knowledge_documents', sa.Column('owner_id', sa.UUID(), nullable=True))
    op.add_column('knowledge_documents', sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'))

    op.create_foreign_key('fk_knowledge_documents_collection', 'knowledge_documents', 'knowledge_collections', ['collection_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_knowledge_documents_folder', 'knowledge_documents', 'knowledge_folders', ['folder_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_knowledge_documents_owner', 'knowledge_documents', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    # 4. Create document versions table
    op.create_table(
        'knowledge_document_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_url', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('change_summary', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Add columns to document_chunks
    op.add_column('document_chunks', sa.Column('chunk_index', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('page_number', sa.Integer(), nullable=True))

    # 6. Create processing jobs table
    op.create_table(
        'knowledge_processing_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('step', sa.String(length=50), nullable=False, server_default='UPLOAD'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Create search history table
    op.create_table(
        'knowledge_search_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('search_type', sa.String(length=50), nullable=False, server_default='SEMANTIC'),
        sa.Column('filters_applied', sa.JSON(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Create saved searches table
    op.create_table(
        'knowledge_saved_searches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('search_type', sa.String(length=50), nullable=False, server_default='SEMANTIC'),
        sa.Column('filters_applied', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Create permissions table
    op.create_table(
        'knowledge_permissions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('collection_id', sa.UUID(), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='VIEWER'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['knowledge_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('knowledge_permissions')
    op.drop_table('knowledge_saved_searches')
    op.drop_table('knowledge_search_history')
    op.drop_table('knowledge_processing_jobs')
    
    op.drop_column('document_chunks', 'chunk_index')
    op.drop_column('document_chunks', 'page_number')

    op.drop_table('knowledge_document_versions')

    op.drop_constraint('fk_knowledge_documents_collection', 'knowledge_documents', type_='foreignkey')
    op.drop_constraint('fk_knowledge_documents_folder', 'knowledge_documents', type_='foreignkey')
    op.drop_constraint('fk_knowledge_documents_owner', 'knowledge_documents', type_='foreignkey')
    
    op.drop_column('knowledge_documents', 'collection_id')
    op.drop_column('knowledge_documents', 'folder_id')
    op.drop_column('knowledge_documents', 'file_size')
    op.drop_column('knowledge_documents', 'storage_url')
    op.drop_column('knowledge_documents', 'is_archived')
    op.drop_column('knowledge_documents', 'is_favorite')
    op.drop_column('knowledge_documents', 'is_pinned')
    op.drop_column('knowledge_documents', 'status')
    op.drop_column('knowledge_documents', 'progress')
    op.drop_column('knowledge_documents', 'error_message')
    op.drop_column('knowledge_documents', 'tags')
    op.drop_column('knowledge_documents', 'category')
    op.drop_column('knowledge_documents', 'department')
    op.drop_column('knowledge_documents', 'owner_id')
    op.drop_column('knowledge_documents', 'current_version')

    op.drop_table('knowledge_folders')
    op.drop_table('knowledge_collections')
