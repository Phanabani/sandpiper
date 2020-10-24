from discord.ext.commands import Bot

from .cog import UnitConversion


def setup(bot: Bot):
    bot.add_cog(UnitConversion(bot))
