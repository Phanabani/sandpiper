from discord.ext.commands import Bot

from .cog import Bios


def setup(bot: Bot):
    bios = Bios(bot)
    bot.add_cog(bios)
