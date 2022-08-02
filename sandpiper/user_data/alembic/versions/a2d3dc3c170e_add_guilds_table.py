"""Add guilds table

Revision ID: a2d3dc3c170e
Revises: e9cf36d27e9d
Create Date: 2021-06-19 04:11:59.436961

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2d3dc3c170e'
down_revision = 'e9cf36d27e9d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'guilds',
        sa.Column('guild_id', sa.BigInteger, primary_key=True),
        sa.Column('birthday_channel', sa.BigInteger),
    )


def downgrade():
    op.drop_table('guilds')
