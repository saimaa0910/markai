"""add_dual_prompt_versioning

Revision ID: c8f9021a3b4e
Revises: b7e8910f45a2
Create Date: 2026-07-21 10:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8f9021a3b4e'
down_revision: Union[str, None] = 'b7e8910f45a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. prompt_versions
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_type', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('variable_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_versions_prompt_id', 'prompt_versions', ['prompt_id'])

    # 2. prompt_releases
    op.create_table(
        'prompt_releases',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('variable_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('published_by', sa.UUID(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['published_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_releases_prompt_id', 'prompt_releases', ['prompt_id'])

    # 3. prompt_version_history
    op.create_table(
        'prompt_version_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prompt_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_version_history_prompt_id', 'prompt_version_history', ['prompt_id'])


def downgrade() -> None:
    op.drop_table('prompt_version_history')
    op.drop_table('prompt_releases')
    op.drop_table('prompt_versions')
