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

    async def on_error(self, event_method: str, *args, **kwargs):
        if event_method == 'on_message':
            msg: discord.Message = args[0]
            logger.error(f'Unhandled in on_message (content: "{msg.content}" author: {msg.author})')
        else:
            logger.error(f"Unhandled in {event_method} (args: {args} kwargs: {kwargs})")
        await super().on_error(event_method, *args, **kwargs)
