from discord.ext.commands import Bot

from .cog import Upgrades


def setup(bot: Bot):
    bot.add_cog(Upgrades(bot))
