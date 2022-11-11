from discord.ext.commands import Bot

from .cog import Upgrades


async def setup(bot: Bot):
    await bot.add_cog(Upgrades(bot))
