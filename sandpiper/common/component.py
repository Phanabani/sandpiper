import abc
from typing import TYPE_CHECKING

import discord

from sandpiper.config import Bot as BotConfig

if TYPE_CHECKING:
    from sandpiper import Components


class Component(abc.ABC):
    def __init__(
        self, client: discord.Client, components: Components, config: BotConfig
    ):
        self.client = client
        self.components = components
        self.config = config

    @abc.abstractmethod
    async def setup(self):
        pass

    @abc.abstractmethod
    async def teardown(self):
        pass
