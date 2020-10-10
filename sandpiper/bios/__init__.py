from discord.ext.commands import Bot

from .cog import UserData


def setup(bot: Bot):
    user_data = UserData(bot)
    bot.add_cog(user_data)
