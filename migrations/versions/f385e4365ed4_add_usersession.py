"""add usersession

Revision ID: f385e4365ed4
Revises: 2d1e822ee1de
Create Date: 2026-10-09 00:47:57.110868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'f385e4365ed4'
down_revision: Union[str, Sequence[str], None] = '2d1e822ee1de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('usersession',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_usersession_user_id_user'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usersession'))
    )
    with op.batch_alter_table('usersession', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_usersession_token'), ['token'], unique=True)



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usersession', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usersession_token'))

    op.drop_table('usersession')
