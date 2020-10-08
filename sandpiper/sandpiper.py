import logging

import discord
from discord.ext.commands import Bot, when_mentioned_or

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
            return when_mentioned_or(config.command_prefix)(bot, msg)

        intents = discord.Intents(
            guilds=True,
            members=True,
            messages=True
        )
        allowed_mentions = discord.AllowedMentions(users=True)
        activity = discord.Game(f'{config.command_prefix} help')

        super().__init__(
            # Client params
            max_messages=None,
            intents=intents,
            allowed_mentions=allowed_mentions,
            activity=activity,
            # Bot params
            command_prefix=get_prefix,
            description=config.description,
        )
        self.load_extension('sandpiper.unit_conversion')
        self.load_extension('sandpiper.user_info')

    async def on_ready(self):
        logger.info('Sandpiper client started')

    async def on_error(self, event_method: str, *args, **kwargs):
        if event_method == 'on_message':
            msg: discord.Message = args[0]
            logger.error(
                f'Unhandled in on_message (content: {msg.content!r} '
                f'author: {msg.author} channel: {msg.channel})',
                exc_info=True
            )
        else:
            logger.error(
                f"Unhandled in {event_method} (args: {args} kwargs: {kwargs})",
                exc_info=True
            )
        await super().on_error(event_method, *args, **kwargs)
