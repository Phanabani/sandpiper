import asyncio
from pathlib import Path
from typing import Optional

from discord.ext.commands import Bot

from .cog import UserData, DatabaseUnavailable
from .database import Database, DatabaseError
from .database_sqlite import DatabaseSQLite
from .enums import PrivacyType

__all__ = [
    'UserData', 'DatabaseUnavailable',
    'Database', 'DatabaseError',
    'DatabaseSQLite',
    'PrivacyType'
]

DB_FILE = Path(__file__).parent.parent / 'sandpiper.db'


def setup(bot: Bot):
    user_data = UserData(bot)
    db = DatabaseSQLite(DB_FILE)
    asyncio.run_coroutine_threadsafe(db.connect(), bot.loop)
    user_data.set_database_adapter(db)
    bot.add_cog(user_data)


async def do_disconnect(user_data: UserData):
    try:
        db = await user_data.get_database()
    except DatabaseUnavailable:
        pass
    else:
        await db.disconnect()


def teardown(bot: Bot):
    """Disconnects from the database"""
    user_data: Optional[UserData] = bot.get_cog('UserData')
    if user_data is not None:
        asyncio.run_coroutine_threadsafe(do_disconnect(user_data), bot.loop)
