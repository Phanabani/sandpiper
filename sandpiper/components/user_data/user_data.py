__all__ = ["UserData", "DatabaseUnavailable"]

import logging

from sandpiper.common.component import Component
from sandpiper.common.paths import MODULE_PATH
from sandpiper.components.user_data import DatabaseSQLite
from sandpiper.components.user_data.database import Database

logger = logging.getLogger("sandpiper.user_data")

DB_FILE = MODULE_PATH / "sandpiper.db"


class DatabaseUnavailable(Exception):
    pass


class UserData(Component):
    _database: Database = None

    async def setup(self):
        db = DatabaseSQLite(DB_FILE)
        await db.connect()
        self.set_database_adapter(db)

        await self.sandpiper.wait_until_ready()
        db.bot_user_id = self.sandpiper.user.id

    async def teardown(self):
        """Disconnects from the database"""
        try:
            db = await self.get_database()
        except DatabaseUnavailable:
            pass
        else:
            await db.disconnect()

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
