from sqlalchemy import Column

from ._types import Snowflake
from .base import Base


class Guild(Base):
    __tablename__ = "guilds"
    __mapper_args__ = {"eager_defaults": True}

    guild_id = Column(Snowflake, primary_key=True)
    birthday_channel = Column(Snowflake)
