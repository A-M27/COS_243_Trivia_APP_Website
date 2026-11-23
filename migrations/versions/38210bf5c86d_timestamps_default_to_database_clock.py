"""timestamps default to database clock

Revision ID: 38210bf5c86d
Revises: d9849c1953ee
Create Date: 2026-10-01 22:52:29.399249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '38210bf5c86d'
down_revision: Union[str, Sequence[str], None] = 'd9849c1953ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('Created_at',
               existing_type=sa.DATETIME(),
               server_default=sa.text('(CURRENT_TIMESTAMP)'),
               existing_nullable=False)
        batch_op.alter_column('Updated_at',
               existing_type=sa.DATETIME(),
               server_default=sa.text('(CURRENT_TIMESTAMP)'),
               existing_nullable=False)

    with op.batch_alter_table('deck', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               server_default=sa.text('(CURRENT_TIMESTAMP)'),
               existing_nullable=False)
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               server_default=sa.text('(CURRENT_TIMESTAMP)'),
               existing_nullable=False)



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('deck', schema=None) as batch_op:
        batch_op.alter_column('updated_at',
               existing_type=sa.DATETIME(),
               server_default=None,
               existing_nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               server_default=None,
               existing_nullable=False)

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('Updated_at',
               existing_type=sa.DATETIME(),
               server_default=None,
               existing_nullable=False)
        batch_op.alter_column('Created_at',
               existing_type=sa.DATETIME(),
               server_default=None,
               existing_nullable=False)

