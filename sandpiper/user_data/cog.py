import logging

import discord.ext.commands as commands

from .database import Database

__all__ = ["UserData", "DatabaseUnavailable"]

logger = logging.getLogger("sandpiper.user_data")


class DatabaseUnavailable(Exception):
    pass


class UserData(commands.Cog):

    _database: Database = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def set_database_adapter(self, database: Database):
        self._database = database

    async def get_database(self):
        """
        Get the database adapter for manipulating user data.

        :returns: The database adapter that has been set with
            ``set_database_adapter``
        :raises DatabaseUnavailable: if database is not set or connected
        """
        if self._database is None:
            raise DatabaseUnavailable("Database adapter is not set.")
        if not await self._database.connected():
            raise DatabaseUnavailable("Database is not connected.")
        await self._database.ready()
        return self._database
