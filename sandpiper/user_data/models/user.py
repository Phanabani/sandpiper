import sqlalchemy as sa
from sqlalchemy import Column, Index

from ._types import Snowflake
from .base import Base
from ..enums import PrivacyType

DEFAULT_PRIVACY = PrivacyType.PRIVATE.value


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("index_users_preferred_name", "preferred_name"),)
    __mapper_args__ = {"eager_defaults": True}

    user_id = Column(Snowflake, primary_key=True)
    preferred_name = Column(sa.String)
    pronouns = Column(sa.String)
    birthday = Column(sa.Date)
    timezone = Column(sa.String)

    privacy_preferred_name = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_pronouns = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_birthday = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_age = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_timezone = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text(str(DEFAULT_PRIVACY))
    )

    last_birthday_notification = Column(sa.DateTime, nullable=True)
