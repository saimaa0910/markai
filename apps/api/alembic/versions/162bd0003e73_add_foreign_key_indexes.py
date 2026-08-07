"""add_foreign_key_indexes

Revision ID: 162bd0003e73
Revises: 162bd0003e72
Create Date: 2026-08-05 14:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '162bd0003e73'
down_revision: Union[str, None] = '77c8719ce9b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for AIModel
    op.create_index('idx_ai_models_provider_id', 'ai_models', ['provider_id'], unique=False)
    
    # Add indexes for AIProviderKey
    op.create_index('idx_ai_provider_keys_provider_id', 'ai_provider_keys', ['provider_id'], unique=False)
    op.create_index('idx_ai_provider_keys_org_id', 'ai_provider_keys', ['organization_id'], unique=False)
    op.create_index('idx_ai_provider_keys_user_id', 'ai_provider_keys', ['user_id'], unique=False)
    
    # Add indexes for AIProviderHealth
    op.create_index('idx_ai_provider_health_provider_id', 'ai_provider_health', ['provider_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_ai_models_provider_id', table_name='ai_models')
    
    op.drop_index('idx_ai_provider_keys_provider_id', table_name='ai_provider_keys')
    op.drop_index('idx_ai_provider_keys_org_id', table_name='ai_provider_keys')
    op.drop_index('idx_ai_provider_keys_user_id', table_name='ai_provider_keys')
    
    op.drop_index('idx_ai_provider_health_provider_id', table_name='ai_provider_health')
