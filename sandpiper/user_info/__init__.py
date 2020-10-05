from discord.ext.commands import Bot

from .cog import UserData


def setup(bot: Bot):
    # TODO instantiate database adapter here?
    bot.add_cog(UserData(bot))


def teardown(bot: Bot):
    """Disconnects from the database"""
    user_data: UserData = bot.get_cog('UserData')
    if user_data.database:
        user_data.database.disconnect()
