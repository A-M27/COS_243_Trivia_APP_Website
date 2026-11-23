"""initial schema

Revision ID: 5992a0794d3b
Revises: 
Create Date: 2026-09-29 21:02:30.672917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '5992a0794d3b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('Username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('First_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Last_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Location', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Timezone', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user'))
    )
    op.create_table('deck',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('User_id', sa.Integer(), nullable=False),
    sa.Column('Visibility', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['User_id'], ['user.id'], name=op.f('fk_deck_User_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_deck'))
    )
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('User_id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Color', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['User_id'], ['user.id'], name=op.f('fk_tag_User_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tag'))
    )
    op.create_table('card',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('Front', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Rear', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('Deck_id', sa.Integer(), nullable=False),
    sa.Column('Card_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('Created_at', sa.DateTime(), nullable=False),
    sa.Column('Updated_at', sa.DateTime(), nullable=False),
    sa.Column('suspended', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['Deck_id'], ['deck.id'], name=op.f('fk_card_Deck_id_deck')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_card'))
    )
    op.create_table('decktaglink',
    sa.Column('deck_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['deck_id'], ['deck.id'], name=op.f('fk_decktaglink_deck_id_deck')),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], name=op.f('fk_decktaglink_tag_id_tag')),
    sa.PrimaryKeyConstraint('deck_id', 'tag_id', name=op.f('pk_decktaglink'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('decktaglink')
    op.drop_table('card')
    op.drop_table('tag')
    op.drop_table('deck')
    op.drop_table('user')
