from discord.ext.commands import Bot

from .conversion import Conversion


async def setup(bot: Bot):
    await bot.add_cog(Conversion(bot))
