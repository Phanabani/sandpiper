"""Rename user_data table to users

Revision ID: e9cf36d27e9d
Revises: 91e18fdd475a
Create Date: 2021-06-19 03:54:11.057297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9cf36d27e9d'
down_revision = '91e18fdd475a'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('user_data', 'users')


def downgrade():
    op.rename_table('users', 'user_data')
