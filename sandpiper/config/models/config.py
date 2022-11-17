from __future__ import annotations

__all__ = ["SandpiperConfig"]

from pydantic import BaseModel

from sandpiper.common.pydantic_helpers import Factory
from sandpiper.config.models.bot import Bot
from sandpiper.config.models.logging import Logging


class SandpiperConfig(BaseModel):
    bot_token: str
    bot: Bot = Factory(Bot)
    logging: Logging = Factory(Logging)
