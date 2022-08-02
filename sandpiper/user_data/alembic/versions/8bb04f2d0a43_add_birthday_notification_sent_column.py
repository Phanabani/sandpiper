"""Add birthday_notification_sent column.

Revision ID: 8bb04f2d0a43
Revises: ecce1f1e8760
Create Date: 2021-07-13 19:23:19.643315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bb04f2d0a43'
down_revision = 'ecce1f1e8760'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column(
            'birthday_notification_sent', sa.Boolean, nullable=False,
            server_default=sa.text('false')
        )
    )


def downgrade():
    op.drop_column('users', 'birthday_notification_sent')
