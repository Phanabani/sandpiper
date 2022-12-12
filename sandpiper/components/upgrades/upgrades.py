__all__ = ["Upgrades", "UpgradeHandler"]

from abc import ABCMeta, abstractmethod
import logging
from typing import Optional, TYPE_CHECKING

from semver import VersionInfo

from sandpiper._version import __version__
from sandpiper.common.component import Component
from sandpiper.components.upgrades.versions import all_upgrade_handlers
from sandpiper.components.user_data import Database, UserData

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)


class Upgrades(Component):
    async def setup(self):
        await self.sandpiper.wait_until_ready()
        await self.do_upgrades()

    async def do_upgrades(self):
        user_data = self.sandpiper.components.user_data
        if user_data is None:
            logger.warning(
                f"Failed to get the UserData component; skipping upgrade handlers."
            )
            return

        db = await user_data.get_database()
        await db.ready()

        previous_version = await db.get_sandpiper_version()
        previous_version = VersionInfo.parse(previous_version or "0.0.0")
        current_version = VersionInfo.parse(__version__)

        if current_version <= previous_version:
            logger.info("No upgrades need to be performed")
            return

        logger.info(
            f"Beginning application upgrade from {previous_version} to "
            f"{current_version}"
        )
        for handler_type in all_upgrade_handlers:
            handler = handler_type(self.sandpiper, previous_version, current_version)
            handler_version = VersionInfo.parse(handler.version())
            if previous_version < handler_version <= current_version:
                # We have upgraded to or past this version; call its upgrade hook
                logger.info(f"Calling upgrade handler {handler}")
                await handler.on_upgrade()

        await db.set_sandpiper_version(current_version)


class UpgradeHandler(metaclass=ABCMeta):
    def __init__(
        self,
        sandpiper: Sandpiper,
        previous_version: VersionInfo,
        current_version: VersionInfo,
    ):
        """
        :param sandpiper: the running instance of Sandpiper
        :param previous_version: the previous version of the application
        :param current_version: the current version of the application
        """
        self.sandpiper = sandpiper
        self.previous_version = previous_version
        self.current_version = current_version

    def __str__(self):
        return (
            f"<UpgradeHandler class={self.__class__.__name__} "
            f"version={self.version()}>"
        )

    async def _get_database(self) -> Optional[Database]:
        user_data: UserData = self.sandpiper.components.user_data
        if user_data is None:
            logger.warning("Failed to get the UserData component")
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
