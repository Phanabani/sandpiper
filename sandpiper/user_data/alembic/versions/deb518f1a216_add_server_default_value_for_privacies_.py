"""Add server default value for privacies, make them not null, and update existing null fields to the default.

Revision ID: deb518f1a216
Revises: a2d3dc3c170e
Create Date: 2021-06-30 11:37:58.636038

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision = 'deb518f1a216'
down_revision = 'a2d3dc3c170e'
branch_labels = None
depends_on = None


def upgrade():
    users = sa.table(
        'users',
        sa.column('privacy_preferred_name', sa.SmallInteger),
        sa.column('privacy_pronouns', sa.SmallInteger),
        sa.column('privacy_birthday', sa.SmallInteger),
        sa.column('privacy_age', sa.SmallInteger),
        sa.column('privacy_timezone', sa.SmallInteger),
    )
    cols = (
        'privacy_preferred_name',
        'privacy_pronouns',
        'privacy_birthday',
        'privacy_age',
        'privacy_timezone'
    )
    for col in cols:
        # Default value of 0 corresponds to PrivacyType.PRIVATE
        op.execute(
            users.update()
            .where(getattr(users.c, col) == op.inline_literal('NULL'))
            .values({col: op.inline_literal(0)})
        )
        op.alter_column(
            'users', col, nullable=False, server_default=sa.text('0')
        )


def downgrade():
    pass
