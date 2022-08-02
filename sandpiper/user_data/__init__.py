from __future__ import annotations

__all__ = [
    'UserData', 'DatabaseUnavailable',
    'Database', 'DatabaseError', 'UserNotInDatabase',
    'DatabaseSQLite',
    'PrivacyType',
    'Pronouns', 'common_pronouns'
]

import asyncio
from pathlib import Path
import typing
from typing import Optional

from discord.ext.commands import Bot

from .cog import UserData, DatabaseUnavailable
from .database import *
from .database_sqlite import DatabaseSQLite
from .enums import PrivacyType
from .pronouns import Pronouns, common_pronouns

if typing.TYPE_CHECKING:
    from sandpiper import Sandpiper

DB_FILE = Path(__file__).parent.parent / 'sandpiper.db'


def setup(bot: Sandpiper):
    user_data = UserData(bot)
    db = DatabaseSQLite(DB_FILE)
    asyncio.run_coroutine_threadsafe(db.connect(), bot.loop)
    user_data.set_database_adapter(db)
    bot.add_cog(user_data)
    bot.add_listener(set_bot_user_id(bot, db), 'on_ready')


def set_bot_user_id(bot: Sandpiper, db: DatabaseSQLite):
    async def fn():
        db.bot_user_id = bot.user.id
    return fn


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
