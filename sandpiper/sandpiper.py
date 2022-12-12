from __future__ import annotations

__all__ = ["Sandpiper", "Components", "run_bot"]

from collections import defaultdict
import logging
import sys
from typing import Callable, Literal

import discord
from discord.app_commands import CommandTree

from sandpiper.components.bios import Bios
from sandpiper.components.birthdays import Birthdays
from sandpiper.components.conversion import Conversion
from sandpiper.components.upgrades import Upgrades
from sandpiper.components.user_data import UserData
from sandpiper.config import Bot as BotConfig
from sandpiper.config.loader import load_config
from sandpiper.help import HelpCommand

logger = logging.getLogger("sandpiper")


class Components:
    bios: Bios | None = None
    birthdays: Birthdays | None = None
    conversion: Conversion | None = None
    upgrades: Upgrades | None = None
    user_data: UserData | None = None

    def __init__(self, sandpiper: Sandpiper):
        self._sandpiper = sandpiper

    async def setup(self):
        self.bios = Bios(self._sandpiper)
        self.birthdays = Birthdays(self._sandpiper)
        self.conversion = Conversion(self._sandpiper)
        self.upgrades = Upgrades(self._sandpiper)
        self.user_data = UserData(self._sandpiper)

        # Other components need UserData, so load it first
        await self.user_data.setup()

        await self.bios.setup()
        await self.birthdays.setup()
        await self.conversion.setup()
        await self.upgrades.setup()

    async def teardown(self):
        # Teardown in reverse order from setup
        await self.bios.teardown()
        await self.birthdays.teardown()
        await self.conversion.teardown()
        await self.upgrades.teardown()

        await self.user_data.teardown()

        self.bios = None
        self.birthdays = None
        self.conversion = None
        self.upgrades = None
        self.user_data = None


T_SupportedListeners = Literal["on_message"]


# noinspection PyMethodMayBeStatic
class Sandpiper(discord.Client):
    def __init__(self, config: BotConfig):

        intents = discord.Intents(
            guilds=True, members=True, messages=True, message_content=True
        )
        allowed_mentions = discord.AllowedMentions(users=True)
        activity = discord.Game(f"hi! c:")

        super().__init__(
            # Client params
            max_messages=None,
            intents=intents,
            allowed_mentions=allowed_mentions,
            activity=activity,
            log_handler=None,
            # Bot params
            description=config.description,
            help_command=HelpCommand(),
        )

        self._sandpiper_listeners = defaultdict(list)
        self.command_tree = CommandTree(self)
        self.components = Components(self)
        self.config = config

    async def setup_hook(self) -> None:
        self.loop.set_debug(True)
        await self.components.setup()

    async def close(self) -> None:
        await self.components.teardown()
        await super().close()

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

    async def add_listener(self, listener_type: T_SupportedListeners, fn: Callable):
        self._sandpiper_listeners[listener_type].append(fn)

    async def on_message(self, message: discord.Message):
        for listener in self._sandpiper_listeners["on_message"]:
            await listener(message)


def run_bot():
    config = load_config()

    # Some extra steps against accidentally leaking the bot token into the
    # public client
    bot_token = config.bot_token
    config.bot_token = ""

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
    sandpiper.run(bot_token)
