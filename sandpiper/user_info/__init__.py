from pathlib import Path

from discord.ext.commands import Bot

from .cog import UserData
from .database_sqlite import DatabaseSQLite

DB_FILE = Path(__file__).parent.parent / 'sandpiper.db'


def setup(bot: Bot):
    # TODO instantiate database adapter here?
    user_data = UserData(bot)
    user_data.set_database_adapter(DatabaseSQLite(DB_FILE))
    bot.add_cog(user_data)


def teardown(bot: Bot):
    """Disconnects from the database"""
    user_data: UserData = bot.get_cog('UserData')
    if user_data.database:
        user_data.database.disconnect()
