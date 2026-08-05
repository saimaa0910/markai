"""upgrade_image_library_v2

Revision ID: 77c8719ce9b7
Revises: 720e36f3966a
Create Date: 2026-08-05 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77c8719ce9b7'
down_revision: Union[str, None] = '720e36f3966a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to ai_image_library
    op.add_column('ai_image_library', sa.Column('file_asset_id', sa.UUID(), nullable=True))
    op.add_column('ai_image_library', sa.Column('parent_id', sa.UUID(), nullable=True))
    op.add_column('ai_image_library', sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'))
    op.add_column('ai_image_library', sa.Column('soft_deleted_at', sa.DateTime(), nullable=True))

    # 2. Add foreign keys
    op.create_foreign_key(
        'fk_image_library_file_asset',
        'ai_image_library', 'file_assets',
        ['file_asset_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_image_library_parent',
        'ai_image_library', 'ai_image_library',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )

    # 3. Create ai_image_collections table
    op.create_table(
        'ai_image_collections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create ai_image_collection_items junction table
    op.create_table(
        'ai_image_collection_items',
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('image_library_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['ai_image_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_library_id'], ['ai_image_library.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('collection_id', 'image_library_id')
    )

    # 5. Create indexes
    op.create_index('ix_image_library_org_id', 'ai_image_library', ['organization_id'])
    op.create_index('ix_image_library_user_id', 'ai_image_library', ['user_id'])
    op.create_index('ix_image_library_campaign_id', 'ai_image_library', ['campaign_id'])
    op.create_index('ix_image_library_run_id', 'ai_image_library', ['run_id'])
    op.create_index('ix_image_library_created_at', 'ai_image_library', ['created_at'])
    op.create_index('ix_image_library_parent_id', 'ai_image_library', ['parent_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_image_library_parent_id', table_name='ai_image_library')
    op.drop_index('ix_image_library_created_at', table_name='ai_image_library')
    op.drop_index('ix_image_library_run_id', table_name='ai_image_library')
    op.drop_index('ix_image_library_campaign_id', table_name='ai_image_library')
    op.drop_index('ix_image_library_user_id', table_name='ai_image_library')
    op.drop_index('ix_image_library_org_id', table_name='ai_image_library')

    # Drop tables
    op.drop_table('ai_image_collection_items')
    op.drop_table('ai_image_collections')

    # Drop constraints
    op.drop_constraint('fk_image_library_parent', 'ai_image_library', type_='foreignkey')
    op.drop_constraint('fk_image_library_file_asset', 'ai_image_library', type_='foreignkey')

    # Drop columns
    op.drop_column('ai_image_library', 'soft_deleted_at')
    op.drop_column('ai_image_library', 'status')
    op.drop_column('ai_image_library', 'parent_id')
    op.drop_column('ai_image_library', 'file_asset_id')
