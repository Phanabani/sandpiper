from discord.ext.commands import Bot

from .cog import Bios


def setup(bot: Bot):
    bot.add_cog(Bios(bot))
