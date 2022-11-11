from sandpiper import Sandpiper
from .cog import Bios


async def setup(bot: Sandpiper):
    config = bot.modules_config.bios
    bios = Bios(bot, allow_public_setting=config.allow_public_setting)
    await bot.add_cog(bios)
