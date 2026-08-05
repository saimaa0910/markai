"""sprint_7_3_provider_settings_and_user_keys

Revision ID: b04a1ac7e2b2
Revises: f1a2b3c4d5e6
Create Date: 2026-08-03 22:02:50.549596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b04a1ac7e2b2'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check columns in ai_providers
    existing_cols_prov = [c['name'] for c in inspector.get_columns('ai_providers')]
    with op.batch_alter_table('ai_providers') as batch_op:
        if 'default_model' not in existing_cols_prov:
            batch_op.add_column(sa.Column('default_model', sa.String(length=100), nullable=True))
        if 'temperature' not in existing_cols_prov:
            batch_op.add_column(sa.Column('temperature', sa.Numeric(precision=4, scale=2), nullable=True, server_default='0.70'))
        if 'max_tokens' not in existing_cols_prov:
            batch_op.add_column(sa.Column('max_tokens', sa.Integer(), nullable=True, server_default='2048'))
        if 'streaming' not in existing_cols_prov:
            batch_op.add_column(sa.Column('streaming', sa.Boolean(), nullable=True, server_default='true'))

    # Check columns in ai_provider_keys
    existing_cols_keys = [c['name'] for c in inspector.get_columns('ai_provider_keys')]
    with op.batch_alter_table('ai_provider_keys') as batch_op:
        if 'user_id' not in existing_cols_keys:
            batch_op.add_column(sa.Column('user_id', sa.UUID(), nullable=True))
            batch_op.create_foreign_key(
                'fk_ai_provider_keys_user_id',
                'users',
                ['user_id'],
                ['id'],
                ondelete='CASCADE'
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Drop user_id foreign key constraint and column from ai_provider_keys if present
    existing_cols_keys = [c['name'] for c in inspector.get_columns('ai_provider_keys')]
    if 'user_id' in existing_cols_keys:
        with op.batch_alter_table('ai_provider_keys') as batch_op:
            batch_op.drop_constraint('fk_ai_provider_keys_user_id', type_='foreignkey')
            batch_op.drop_column('user_id')

    # Drop settings columns from ai_providers if present
    existing_cols_prov = [c['name'] for c in inspector.get_columns('ai_providers')]
    with op.batch_alter_table('ai_providers') as batch_op:
        if 'streaming' in existing_cols_prov:
            batch_op.drop_column('streaming')
        if 'max_tokens' in existing_cols_prov:
            batch_op.drop_column('max_tokens')
        if 'temperature' in existing_cols_prov:
            batch_op.drop_column('temperature')
        if 'default_model' in existing_cols_prov:
            batch_op.drop_column('default_model')
