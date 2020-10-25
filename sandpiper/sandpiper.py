import logging
import sys

import discord
import discord.ext.commands as commands

from . import Config

__all__ = ['Sandpiper']

logger = logging.getLogger('sandpiper')


class Sandpiper(commands.Bot):

    def __init__(self, config: Config.Bot):

        # noinspection PyUnusedLocal
        def get_prefix(bot: commands.Bot, msg: discord.Message) -> str:
            """Allows prefix-less command invocation in DMs"""
            if isinstance(msg.channel, discord.DMChannel):
                return ''
            return commands.when_mentioned_or(config.command_prefix)(bot, msg)

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

        @self.command(name=config.command_prefix.strip())
        async def noprefix_notify(ctx: commands.Context, *, rest: str):
            if ctx.prefix == '':
                raise commands.BadArgument(
                    f'You don\'t need to prefix commands here. '
                    f'Just type "{rest}".')

        self.load_extension('sandpiper.user_info')
        self.load_extension('sandpiper.bios')
        self.load_extension('sandpiper.conversion')

    async def on_connect(self):
        logger.info('Client connected')

    async def on_disconnect(self):
        logger.info('Client disconnected')

    async def on_resumed(self):
        logger.info('Session resumed')

    async def on_ready(self):
        logger.info('Client started')

    async def on_error(self, event_method: str, *args, **kwargs):
        exc_type, __, __ = sys.exc_info()

        if exc_type is discord.HTTPException:
            logger.warning('HTTP exception', exc_info=True)
        elif exc_type is discord.Forbidden:
            logger.warning('Forbidden request', exc_info=True)

        elif event_method == 'on_message':
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
