"""add user password_hash

Revision ID: 2d1e822ee1de
Revises: 38210bf5c86d
Create Date: 2026-10-08 07:59:24.611329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '2d1e822ee1de'
down_revision: Union[str, Sequence[str], None] = '38210bf5c86d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=True))



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_hash')

