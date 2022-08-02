"""Add sandpiper_meta table.

Revision ID: 643337f23b38
Revises: 8bb04f2d0a43
Create Date: 2021-07-21 00:45:39.063663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '643337f23b38'
down_revision = '8bb04f2d0a43'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sandpiper_meta',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('version', sa.String)
    )


def downgrade():
    op.drop_table('sandpiper_meta')
