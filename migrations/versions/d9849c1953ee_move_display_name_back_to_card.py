"""move display_name back to card

Revision ID: d9849c1953ee
Revises: 1bb0375a4941
Create Date: 2026-10-01 22:45:50.605874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'd9849c1953ee'
down_revision: Union[str, Sequence[str], None] = '1bb0375a4941'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('display_name')



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_name', sa.VARCHAR(), nullable=True))

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('display_name')

