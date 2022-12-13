from __future__ import annotations

__all__ = ["UpgradeHandler"]

from abc import ABCMeta, abstractmethod
import logging
from typing import Optional, TYPE_CHECKING

from semver import VersionInfo

from sandpiper.common.logging import warn_component_none
from sandpiper.components.user_data import Database, UserData

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)


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
            return warn_component_none(logger, "UserData")
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
