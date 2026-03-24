"""add title_ko and summary_ko to updates

Revision ID: c3a7b9d1e5f2
Revises: af1a588bcca2
Create Date: 2026-03-24 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3a7b9d1e5f2'
down_revision: Union[str, Sequence[str], None] = 'af1a588bcca2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('updates', sa.Column('title_ko', sa.Text(), nullable=True))
    op.add_column('updates', sa.Column('summary_ko', sa.Text(), nullable=True))
    # Convert update_type from single string to JSONB list for multi-select
    op.alter_column('updates', 'update_type',
                     type_=sa.dialects.postgresql.JSONB(),
                     postgresql_using='CASE WHEN update_type IS NOT NULL '
                                      "THEN jsonb_build_array(update_type) "
                                      'ELSE NULL END')


def downgrade() -> None:
    op.alter_column('updates', 'update_type',
                     type_=sa.String(),
                     postgresql_using='update_type->>0')
    op.drop_column('updates', 'summary_ko')
    op.drop_column('updates', 'title_ko')
