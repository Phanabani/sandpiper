from abc import ABCMeta, abstractmethod

import discord.ext.commands as commands
from semver import VersionInfo

__all__ = ['UpgradeHandlerBase', 'do_upgrades']


class UpgradeHandlerBase(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def version(cls) -> str:
        """The version identifier for this upgrade"""
        pass

    @classmethod
    @abstractmethod
    async def on_upgrade(
            cls, bot: commands.Bot, previous_version: VersionInfo,
            current_version: VersionInfo
    ):
        """
        Perform tasks upon an application upgrade.

        :param bot: the running Discord bot
        :param previous_version: the previous version of the application
        :param current_version: the current version of the application
        """
        pass


async def do_upgrades(
        bot: commands.Bot, previous_version: str, current_version: str,
        upgrade_handlers: list[UpgradeHandlerBase]
):
    previous_version = VersionInfo.parse(previous_version)
    current_version = VersionInfo.parse(current_version)
    if current_version <= previous_version:
        return

    for handler in upgrade_handlers:
        handler_version = VersionInfo.parse(handler.version())
        if previous_version < handler_version <= current_version:
            await handler.on_upgrade(bot, previous_version, current_version)
