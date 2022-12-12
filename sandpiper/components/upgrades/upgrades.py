__all__ = ["Upgrades"]

import logging

from semver import VersionInfo

from sandpiper._version import __version__
from sandpiper.common.component import Component
from sandpiper.components.upgrades.versions import all_upgrade_handlers

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
