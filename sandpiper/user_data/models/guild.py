import sqlalchemy as sa
from sqlalchemy import Column

from .base import Base


class Guild(Base):
    __tablename__ = 'guilds'
    __mapper_args__ = {'eager_defaults': True}

    guild_id = Column(sa.BigInteger, primary_key=True)
    birthday_channel = Column(sa.BigInteger)
