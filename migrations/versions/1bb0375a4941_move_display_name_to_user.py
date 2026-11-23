"""move display_name to user

Revision ID: 1bb0375a4941
Revises: 3b42fea37a30
Create Date: 2026-10-01 22:19:00.525011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '1bb0375a4941'
down_revision: Union[str, Sequence[str], None] = '3b42fea37a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('display_name')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('display_name')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_name', sa.VARCHAR(), nullable=True))

