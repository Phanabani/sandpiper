import logging

import discord
from discord.ext.commands import Bot

from . import Config

__all__ = ['Sandpiper']

logger = logging.getLogger('sandpiper')


class Sandpiper(Bot):

    def __init__(self, config: Config.Bot):

        # noinspection PyUnusedLocal
        def get_prefix(bot: Bot, msg: discord.Message) -> str:
            """Allows prefix-less command invocation in DMs"""
            if isinstance(msg.channel, discord.DMChannel):
                return ''
            return config.command_prefix

        super().__init__(
            command_prefix=get_prefix,
            description=config.description
        )
        self.load_extension('sandpiper.unit_conversion')
        self.load_extension('sandpiper.user_info')

    async def on_ready(self):
        logger.info('Sandpiper client started')
