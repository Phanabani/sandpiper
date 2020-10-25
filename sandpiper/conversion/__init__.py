from discord.ext.commands import Bot

from .cog import Conversion


def setup(bot: Bot):
    bot.add_cog(Conversion(bot))
