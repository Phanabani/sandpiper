from discord.ext import commands as commands
from semver import VersionInfo

from ..upgrades import UpgradeHandlerBase


class Sandpiper_1_6_0(UpgradeHandlerBase):

    @classmethod
    def version(cls) -> str:
        return '1.6.0'

    @classmethod
    async def on_upgrade(
            cls, bot: commands.Bot, previous_version: VersionInfo,
            current_version: VersionInfo
    ):
        pass
