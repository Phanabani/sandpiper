from contextlib import AbstractAsyncContextManager
import datetime as dt
import logging
from pathlib import Path
from typing import Annotated, Callable, Optional, Union, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from sandpiper.common.time import TimezoneType
from sandpiper.user_data.database import Database
from sandpiper.user_data.enums import PrivacyType
from sandpiper.user_data.models import Base

logger = logging.getLogger(__name__)

T_Sessionmaker = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class DatabaseSQLAlchemy(Database):

    _connected: bool = False
    _engine: Optional[AsyncEngine] = None
    _session_maker: Optional[T_Sessionmaker] = None
    db_path: Union[str, Path]

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path.absolute()

    async def connect(self):
        logger.info(f"Connecting to database (path={self.db_path})")
        if self._connected:
            raise RuntimeError("Database is already connected")

        self._connected = True
        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}",
            echo=True, future=True
        )
        self._session_maker = cast(T_Sessionmaker, sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        ))
        await self.create_tables()

    async def disconnect(self):
        logger.info(f"Disconnecting from database (path={self.db_path})")
        if not self._connected:
            raise RuntimeError("Database is not connected")
        self._connected = False
        await self._engine.close()
        self._engine = None
        self._session_maker = None

    async def connected(self) -> bool:
        return self._connected

    async def create_tables(self):
        logger.info("Creating database tables if they don't exist")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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
