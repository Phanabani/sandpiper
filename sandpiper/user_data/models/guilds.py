import sqlalchemy as sa
from sqlalchemy import Column

from .base import Base


class Guilds(Base):
    __tablename__ = 'guilds'
    __mapper_args__ = {'eager_defaults': True}

    guild_id = Column(sa.BigInteger, primary_key=True)
    announcement_channel = Column(sa.BigInteger)
