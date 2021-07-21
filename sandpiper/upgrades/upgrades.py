from abc import ABCMeta, abstractmethod
import logging
from typing import Optional, Type

import discord.ext.commands as commands
from semver import VersionInfo

from sandpiper.user_data import Database, UserData

__all__ = ['UpgradeHandler', 'do_upgrades']

logger = logging.getLogger(__name__)


class UpgradeHandler(metaclass=ABCMeta):

    def __init__(
            self, bot: commands.Bot, previous_version: VersionInfo,
            current_version: VersionInfo
    ):
        """
        :param bot: the running Discord bot
        :param previous_version: the previous version of the application
        :param current_version: the current version of the application
        """
        self.bot = bot
        self.previous_version = previous_version
        self.current_version = current_version

    def __str__(self):
        return (
            f"<UpgradeHandler class={self.__class__.__name__} "
            f"version={self.version()}>"
        )

    async def _get_database(self) -> Optional[Database]:
        user_data: UserData = self.bot.get_cog('UserData')
        if user_data is None:
            logger.warning("Failed to load the UserData cog")
            return None
        db = await user_data.get_database()
        await db.ready()
        return db

    @abstractmethod
    def version(self) -> str:
        """The version identifier for this upgrade"""
        pass

    @abstractmethod
    async def on_upgrade(self):
        """
        Perform tasks upon an application upgrade.
        """
        pass


async def do_upgrades(
        bot: commands.Bot, previous_version: Optional[str],
        current_version: str, upgrade_handlers: list[Type[UpgradeHandler]]
):
    previous_version = VersionInfo.parse(previous_version or '0.0.0')
    current_version = VersionInfo.parse(current_version)
    logger.info(
        f"Beginning application upgrade from {previous_version} to "
        f"{current_version}"
    )
    if current_version <= previous_version:
        logger.info("No upgrades need to be performed")
        return

    for handler_type in upgrade_handlers:
        handler = handler_type(bot, previous_version, current_version)
        handler_version = VersionInfo.parse(handler.version())
        if previous_version < handler_version <= current_version:
            # We have upgraded to or past this version; call its upgrade hook
            logger.info(f"Calling upgrade handler {handler}")
            await handler.on_upgrade()
