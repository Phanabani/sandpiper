"""Init

Revision ID: 91e18fdd475a
Revises: 
Create Date: 2021-06-18 20:33:16.845929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "91e18fdd475a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_data",
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column("preferred_name", sa.String),
        sa.Column("pronouns", sa.String),
        sa.Column("birthday", sa.Date),
        sa.Column("timezone", sa.String),
        sa.Column("privacy_preferred_name", sa.SmallInteger),
        sa.Column("privacy_pronouns", sa.SmallInteger),
        sa.Column("privacy_birthday", sa.SmallInteger),
        sa.Column("privacy_age", sa.SmallInteger),
        sa.Column("privacy_timezone", sa.SmallInteger),
    )
    op.create_index(
        "index_users_preferred_name", "user_data", ["preferred_name"], unique=False
    )


def downgrade():
    op.drop_index("index_users_preferred_name", table_name="user_data")
    op.drop_table("user_data")
