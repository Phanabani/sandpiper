import sqlalchemy as sa
from sqlalchemy import Column, Index

from .base import Base
from ..enums import PrivacyType

DEFAULT_PRIVACY = PrivacyType.PRIVATE.value


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('index_users_preferred_name', 'preferred_name'),
    )
    __mapper_args__ = {'eager_defaults': True}

    # Could be BigInteger in other database backends, but not SQLite because
    # 64-bit ints are signed. :(
    # This realistically won't even be a problem until like year 2084, but
    # we might as well use a good practice.
    #
    # ceil(log10((1<<64) - 1)) == 20 (AKA the number of bytes required to
    # represent the decimal form of the highest 64-bit unsigned int)
    user_id = Column(sa.String(20), primary_key=True)
    preferred_name = Column(sa.String)
    pronouns = Column(sa.String)
    birthday = Column(sa.Date)
    timezone = Column(sa.String)

    privacy_preferred_name = Column(
        sa.SmallInteger, nullable=False,
        server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_pronouns = Column(
        sa.SmallInteger, nullable=False,
        server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_birthday = Column(
        sa.SmallInteger, nullable=False,
        server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_age = Column(
        sa.SmallInteger, nullable=False,
        server_default=sa.text(str(DEFAULT_PRIVACY))
    )
    privacy_timezone = Column(
        sa.SmallInteger, nullable=False,
        server_default=sa.text(str(DEFAULT_PRIVACY))
    )
