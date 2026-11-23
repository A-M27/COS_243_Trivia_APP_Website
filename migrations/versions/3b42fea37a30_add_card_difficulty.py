"""add card difficulty

Revision ID: 3b42fea37a30
Revises: 389e226b9d5f
Create Date: 2026-10-01 22:06:33.725757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '3b42fea37a30'
down_revision: Union[str, Sequence[str], None] = '389e226b9d5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('difficulty', sa.Integer(), server_default='3', nullable=False))
        batch_op.add_column(sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('display_name')
        batch_op.drop_column('difficulty')

