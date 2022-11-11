"""Promote snowflake fields from integers to strings, since SQLite only stores signed 64-bit ints.

Revision ID: ecce1f1e8760
Revises: deb518f1a216
Create Date: 2021-07-01 17:31:15.365738

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ecce1f1e8760"
down_revision = "deb518f1a216"
branch_labels = None
depends_on = None


def upgrade():
    """
    Could be BigInteger in other database backends, but not SQLite because
    64-bit ints are signed. :(
    This realistically won't even be a problem until like year 2084, but
    we might as well use a good practice.

    ceil(log10((1<<64) - 1)) == 20 (AKA the number of bytes required to
    represent the decimal form of the highest 64-bit unsigned int)
    """

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(20))

    with op.batch_alter_table("guilds") as batch_op:
        batch_op.alter_column("guild_id", type_=sa.String(20))
        batch_op.alter_column("birthday_channel", type_=sa.String(20))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("user_id", type_=sa.BigInteger)

    with op.batch_alter_table("guilds") as batch_op:
        batch_op.alter_column("guild_id", type_=sa.BigInteger)
        batch_op.alter_column("birthday_channel", type_=sa.BigInteger)
