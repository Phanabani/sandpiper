"""Rename birthday_notification_sent to last_birthday_notification. Promote to datetime.

Revision ID: eaa603d93189
Revises: 643337f23b38
Create Date: 2021-08-07 23:39:00.392785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eaa603d93189'
down_revision = '643337f23b38'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('birthday_notification_sent')
        batch_op.add_column(
            sa.Column('last_birthday_notification', sa.DateTime, nullable=True)
        )


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('last_birthday_notification')
        batch_op.add_column(
            sa.Column(
                'birthday_notification_sent', sa.Boolean, nullable=False,
                server_default=sa.text('false')
            )
        )
