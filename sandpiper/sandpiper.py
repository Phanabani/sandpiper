from __future__ import annotations

__all__ = ["Sandpiper", "Components", "run_bot"]

from asyncio import Task
from collections import defaultdict
from collections.abc import Coroutine
import logging
import sys
from typing import Callable, Literal, TypeVar

import discord
from discord.app_commands import Command, CommandTree, ContextMenu, Group

from sandpiper.common.component import Component, MissingComponentError
from sandpiper.components.bios import Bios
from sandpiper.components.birthdays import Birthdays
from sandpiper.components.conversion import Conversion
from sandpiper.components.upgrades import Upgrades
from sandpiper.components.user_data import UserData
from sandpiper.config import Bot as BotConfig
from sandpiper.config.loader import load_config
from sandpiper.help import HelpCommand

logger = logging.getLogger("sandpiper")

T_Component = TypeVar("T_Component", bound=Component)


class Components:
    _bios: Bios | None = None
    _birthdays: Birthdays | None = None
    _conversion: Conversion | None = None
    _upgrades: Upgrades | None = None
    _user_data: UserData | None = None

    def __init__(self, sandpiper: Sandpiper):
        self._sandpiper = sandpiper
        self._setup_task_ref: Task | None = None
        self._teardown_task_ref: Task | None = None

    @staticmethod
    def try_get(attr: T_Component | None, type_: type[T_Component]) -> T_Component:
        if attr is None:
            raise MissingComponentError(type_.__name__)
        return attr

    @property
    def bios(self) -> Bios:
        return self.try_get(self._bios, Bios)

    @property
    def birthdays(self) -> Birthdays:
        return self.try_get(self._birthdays, Birthdays)

    @property
    def conversion(self) -> Conversion:
        return self.try_get(self._conversion, Conversion)

    @property
    def upgrades(self) -> Upgrades:
        return self.try_get(self._upgrades, Upgrades)

    @property
    def user_data(self) -> UserData:
        return self.try_get(self._user_data, UserData)

    async def _create_task(self, fn: Coroutine) -> Task:
        return self._sandpiper.loop.create_task(fn)

    async def setup(self):
        self._setup_task_ref = self._sandpiper.loop.create_task(self._setup_task())

    async def _setup_task(self):
        logger.debug("Setting up components")

        if self._teardown_task_ref:
            self._teardown_task_ref.cancel()
            self._teardown_task_ref = None

        self._bios = Bios(self._sandpiper)
        self._birthdays = Birthdays(self._sandpiper)
        self._conversion = Conversion(self._sandpiper)
        self._upgrades = Upgrades(self._sandpiper)
        self._user_data = UserData(self._sandpiper)

        # Other components need UserData, so load it first
        await self._user_data.setup()

        await self._bios.setup()
        await self._birthdays.setup()
        await self._conversion.setup()
        await self._upgrades.setup()

        await self._sandpiper.on_components_setup_complete()

        logger.debug("Component setup complete")

    async def teardown(self):
        self._teardown_task_ref = self._create_task(self._teardown_task())

    async def _teardown_task(self):
        logger.debug("Tearing down components")

        if self._setup_task_ref:
            self._setup_task_ref.cancel()
            self._setup_task_ref = None

        # Teardown in reverse order from setup
        await self._bios.teardown()
        await self._birthdays.teardown()
        await self._conversion.teardown()
        await self._upgrades.teardown()

        await self._user_data.teardown()

        self._bios = None
        self._birthdays = None
        self._conversion = None
        self._upgrades = None
        self._user_data = None

        logger.debug("Component teardown complete")


T_SupportedListeners = Literal["on_message"]


# noinspection PyMethodMayBeStatic
class Sandpiper(discord.Client):
    def __init__(self, config: BotConfig):

        intents = discord.Intents(
            guilds=True, members=True, messages=True, message_content=True
        )
        allowed_mentions = discord.AllowedMentions(users=True)
        activity = discord.Game("with twigs")

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
        self._command_tree = CommandTree(self)
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

    async def on_components_setup_complete(self):
        logger.info("Syncing commands")
        for guild in self.config.commands.guilds:
            await self._command_tree.sync(guild=guild)

    def add_listener(self, listener_type: T_SupportedListeners, fn: Callable):
        self._sandpiper_listeners[listener_type].append(fn)

    def add_command(self, command: Command | ContextMenu | Group, /):
        logger.debug(f"Adding command {command}")
        self._command_tree.add_command(
            command, guilds=self.config.commands.guilds, override=True
        )

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
    sandpiper.run(bot_token, log_handler=None)
