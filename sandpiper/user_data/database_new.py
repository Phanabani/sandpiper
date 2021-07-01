from contextlib import AbstractAsyncContextManager
import datetime as dt
import logging
from pathlib import Path
from typing import Annotated, Callable, Optional, Union, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncConnection, AsyncEngine, AsyncSession, create_async_engine
)
from sqlalchemy.orm import sessionmaker

from sandpiper.common.time import TimezoneType
import sandpiper.user_data.alembic_utils as alembic_utils
from sandpiper.user_data.database import Database
from sandpiper.user_data.enums import PrivacyType
from sandpiper.user_data.models import Base, Guild, User

logger = logging.getLogger(__name__)

T_Sessionmaker = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class DatabaseSQLite(Database):

    _connected: bool = False
    _engine: Optional[AsyncEngine] = None
    _session_maker: Optional[T_Sessionmaker] = None
    db_path: Union[str, Path]

    def __init__(self, db_path: Union[str, Path]):
        if isinstance(db_path, Path):
            db_path = db_path.absolute()
        self.db_path = db_path

    async def connect(self):
        logger.info(f"Connecting to database (path={self.db_path})")
        if self._connected:
            raise RuntimeError("Database is already connected")

        self._connected = True
        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}", echo=False, future=True
        )
        self._session_maker = cast(T_Sessionmaker, sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        ))
        await self._do_upgrades()

    async def disconnect(self):
        logger.info(f"Disconnecting from database (path={self.db_path})")
        if not self._connected:
            raise RuntimeError("Database is not connected")
        self._connected = False
        await self._engine.dispose()
        self._engine = None
        self._session_maker = None

    async def connected(self) -> bool:
        return self._connected

    async def _do_upgrades(self):
        revision = await alembic_utils.get_current_heads(self._engine)
        if revision:
            logger.info("Performing Alembic upgrade to head (may be a no-op)")
            await alembic_utils.upgrade(self._engine, 'head')
            return

        logger.info("Database has no Alembic version")
        async with self._engine.begin() as conn:
            # Check the sqlite meta table for table definitions
            conn: AsyncConnection
            no_tables = (await conn.execute(sa.text(
                "SELECT 1 FROM sqlite_master LIMIT 1"
            ))).first() is None
            user_data_table_exists = (await conn.execute(sa.text(
                "SELECT 1 FROM sqlite_master WHERE name = 'user_data' LIMIT 1"
            ))).first() is not None

        if no_tables:
            # This database is empty, we can create all and stamp as head
            logger.info(
                "Empty database; creating all and stamping as Alembic head"
            )
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await alembic_utils.stamp(self._engine, 'head')

        elif user_data_table_exists:
            # The database already existed but was not tracked yet by Alembic.
            # This means the database is aligned with the init migration.
            # Stamp it as such so we can then apply migrations to it.
            logger.info(
                "user_data table found; stamping with the appropriate "
                "Alembic revision to continue with upgrades"
            )
            await alembic_utils.stamp(self._engine, '91e18fdd475a')
            logger.info("Upgrading to head")
            await alembic_utils.upgrade(self._engine, 'head')

        else:
            err_msg = (
                f"Database is in an unexpected state. There appears to be "
                f"data in it but it is untracked by Alembic and it cannot "
                f"be automatically handled. You may have to manually stamp "
                f"the Alembic revision."
            )
            logger.fatal(err_msg)
            raise RuntimeError(err_msg)

        logger.info("Upgrade complete")

    async def delete_user(self, user_id: int):
        pass

    async def get_preferred_name(self, user_id: int) -> Optional[str]:
        pass

    async def set_preferred_name(
            self, user_id: int, new_preferred_name: Optional[str]
    ):
        pass

    async def get_privacy_preferred_name(self, user_id: int) -> PrivacyType:
        pass

    async def set_privacy_preferred_name(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    async def find_users_by_preferred_name(
            self, name: str
    ) -> list[tuple[int, str]]:
        pass

    async def get_pronouns(self, user_id: int) -> Optional[str]:
        pass

    async def set_pronouns(self, user_id: int, new_pronouns: Optional[str]):
        pass

    async def get_privacy_pronouns(self, user_id: int) -> PrivacyType:
        pass

    async def set_privacy_pronouns(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    async def get_birthday(self, user_id: int) -> Optional[dt.date]:
        pass

    async def set_birthday(
            self, user_id: int, new_birthday: Optional[dt.date]
    ):
        pass

    async def get_privacy_birthday(self, user_id: int) -> PrivacyType:
        pass

    async def set_privacy_birthday(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    async def get_birthdays_range(
            self, start: dt.date, end: dt.date
    ) -> list[tuple[Annotated[int, 'user_id'], dt.date]]:
        pass

    async def get_privacy_age(self, user_id: int) -> PrivacyType:
        pass

    async def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        pass

    async def get_timezone(self, user_id: int) -> Optional[TimezoneType]:
        pass

    async def set_timezone(
            self, user_id: int, new_timezone: Optional[TimezoneType]
    ):
        pass

    async def get_privacy_timezone(self, user_id: int) -> PrivacyType:
        pass

    async def set_privacy_timezone(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    async def get_all_timezones(self) -> list[tuple[int, TimezoneType]]:
        pass

    async def get_guild_announcement_channel(
            self, guild_id: int
    ) -> Optional[int]:
        pass
