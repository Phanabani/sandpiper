import sqlalchemy as sa
from sqlalchemy import Column, Index

from .base import Base


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('index_users_preferred_name', 'preferred_name'),
    )
    __mapper_args__ = {'eager_defaults': True}

    user_id = Column(sa.BigInteger, primary_key=True)
    preferred_name = Column(sa.String)
    pronouns = Column(sa.String)
    birthday = Column(sa.Date)
    timezone = Column(sa.String)

    privacy_preferred_name = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text('0')
    )
    privacy_pronouns = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text('0')
    )
    privacy_birthday = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text('0')
    )
    privacy_age = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text('0')
    )
    privacy_timezone = Column(
        sa.SmallInteger, nullable=False, server_default=sa.text('0')
    )
