"""unique user email

Revision ID: 389e226b9d5f
Revises: 5992a0794d3b
Create Date: 2026-09-29 21:23:44.207634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '389e226b9d5f'
down_revision: Union[str, Sequence[str], None] = '5992a0794d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_user_email'), ['email'])



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_user_email'), type_='unique')

