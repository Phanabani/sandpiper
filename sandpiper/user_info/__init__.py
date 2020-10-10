from pathlib import Path
from typing import Optional

from discord.ext.commands import Bot

from .cog import UserData, DatabaseUnavailable
from .database_sqlite import DatabaseSQLite

DB_FILE = Path(__file__).parent.parent / 'sandpiper.db'


def setup(bot: Bot):
    user_data = UserData(bot)
    user_data.set_database_adapter(DatabaseSQLite(DB_FILE))
    bot.add_cog(user_data)


def teardown(bot: Bot):
    """Disconnects from the database"""
    user_data: Optional[UserData] = bot.get_cog('UserData')
    if user_data is not None:
        try:
            user_data.get_database().disconnect()
        except DatabaseUnavailable:
            pass
