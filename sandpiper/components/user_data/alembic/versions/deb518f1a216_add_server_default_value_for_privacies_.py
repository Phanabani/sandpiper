"""
Add server default value for privacies, make them not null, and update existing
null fields to the default.

Revision ID: deb518f1a216
Revises: a2d3dc3c170e
Create Date: 2021-06-30 11:37:58.636038

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.

revision = "deb518f1a216"
down_revision = "a2d3dc3c170e"
branch_labels = None
depends_on = None

DEFAULT_PRIVACY = 0  # == PrivacyType.PRIVATE
privacy_cols = (
    "privacy_preferred_name",
    "privacy_pronouns",
    "privacy_birthday",
    "privacy_age",
    "privacy_timezone",
)
# Build a little fake table with our privacy columns so we can update them
users = sa.table(
    "users",
    *[sa.column(col, sa.SmallInteger) for col in privacy_cols],
)


# noinspection PyComparisonWithNone
def upgrade():
    # We need this connection for the update to work... for some reason.
    # op.execute wasn't working
    conn: Connection = op.get_bind()

    with op.batch_alter_table("users") as batch_op:
        for col in privacy_cols:
            # Replace all null fields with the new default value of 0 (which
            # was already being returned programmatically as the default)
            conn.execute(
                users.update()
                .where(getattr(users.c, col) == None)
                .values({col: DEFAULT_PRIVACY})
            )
            # Then make the field non-nullable, and set the server-side default
            # With the SQLite backend, this op is going to create an entirely
            # new table and copy all data over because SQLite doesn't have much
            # functionality in terms of alter column :(
            batch_op.alter_column(
                col, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
            )


def downgrade():
    # The replacement of null fields with the new default is destructive but
    # backwards-compatible, so we will not be doing anything about that change
    with op.batch_alter_table("users") as batch_op:
        for col in privacy_cols:
            batch_op.alter_column(col, nullable=True, server_default=None)
