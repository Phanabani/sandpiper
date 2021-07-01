import sqlalchemy as sa
from sqlalchemy import Column

from .base import Base


class Guild(Base):
    __tablename__ = 'guilds'
    __mapper_args__ = {'eager_defaults': True}

    # See comment in the User model for why our columns are defined like this
    guild_id = Column(sa.String(20), primary_key=True)
    birthday_channel = Column(sa.String(20))
