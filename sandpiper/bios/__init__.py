from .cog import Bios
from sandpiper import Sandpiper


def setup(bot: Sandpiper):
    config = bot.modules_config.bios
    bios = Bios(bot, allow_public_setting=config.allow_public_setting)
    bot.add_cog(bios)
