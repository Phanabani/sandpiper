import logging
from pathlib import Path
import sys

import discord
import discord.ext.commands as commands

from .config import SandpiperConfig
from .help import HelpCommand

__all__ = ("Sandpiper", "run_bot")

logger = logging.getLogger("sandpiper")


# noinspection PyMethodMayBeStatic
class Sandpiper(commands.Bot):
    def __init__(self, config: SandpiperConfig._Bot):

        # noinspection PyUnusedLocal
        def get_prefix(bot: commands.Bot, msg: discord.Message) -> str:
            """Allows prefix-less command invocation in DMs"""
            if isinstance(msg.channel, discord.DMChannel):
                return ""
            return commands.when_mentioned_or(config.command_prefix)(bot, msg)

        intents = discord.Intents(guilds=True, members=True, messages=True)
        allowed_mentions = discord.AllowedMentions(users=True)
        activity = discord.Game(f"{config.command_prefix}help")

        super().__init__(
            # Client params
            max_messages=None,
            intents=intents,
            allowed_mentions=allowed_mentions,
            activity=activity,
            log_handler=None,
            # Bot params
            command_prefix=get_prefix,
            description=config.description,
            help_command=HelpCommand(),
        )

        # Add a dummy command that triggers when the user tries to use the
        # command prefix in DMs. It's not required in DMs, so it'll tell the
        # user to just omit it
        @self.command(name=config.command_prefix.strip(), hidden=True)
        async def noprefix_notify(ctx: commands.Context, *, rest: str):
            if ctx.prefix == "":
                raise commands.BadArgument(
                    f"You don't need to prefix commands here. " f"Just type `{rest}`."
                )

        self.modules_config = config.modules

        self.load_extension("sandpiper.user_data")
        self.load_extension("sandpiper.bios")
        self.load_extension("sandpiper.birthdays")
        self.load_extension("sandpiper.conversion")
        self.load_extension("sandpiper.upgrades")

    async def on_connect(self):
        logger.info("Client connected")

    async def on_disconnect(self):
        logger.info("Client disconnected")

    async def on_resumed(self):
        logger.info("Session resumed")

    async def on_ready(self):
        logger.info("Client started")

    async def on_error(self, event_method: str, *args, **kwargs):
        exc_type, __, __ = sys.exc_info()

        if exc_type is discord.HTTPException:
            logger.warning("HTTP exception", exc_info=True)
        elif exc_type is discord.Forbidden:
            logger.warning("Forbidden request", exc_info=True)

        elif event_method == "on_message":
            msg: discord.Message = args[0]
            logger.error(
                f"Unhandled in on_message (content: {msg.content!r} "
                f"author: {msg.author} channel: {msg.channel})",
                exc_info=True,
            )
        else:
            logger.error(
                f"Unhandled in {event_method} (args: {args} kwargs: {kwargs})",
                exc_info=True,
            )


def run_bot():
    # Load config
    config_path = Path(__file__).parent / "config.json"
    with config_path.open() as f:
        config = SandpiperConfig(f)

    # Some extra steps against accidentally leaking the bot token into the
    # public client
    bot_token = config.bot_token
    config.bot_token = None

    # Sandpiper logging
    logger = logging.getLogger("sandpiper")
    logger.setLevel(config.logging.sandpiper_logging_level)
    logger.addHandler(config.logging.handler)

    # Discord logging
    logger = logging.getLogger("discord")
    logger.setLevel(config.logging.discord_logging_level)
    logger.addHandler(config.logging.handler)

    # Run bot
    sandpiper = Sandpiper(config.bot)
    sandpiper.loop.set_debug(True)
    sandpiper.run(bot_token)
