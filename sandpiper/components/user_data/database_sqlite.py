import asyncio
from contextlib import AbstractAsyncContextManager
import datetime as dt
import logging
from pathlib import Path
from typing import Annotated, Any, Callable, Optional, Union, cast

import pytz
import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from sandpiper.common.time import TimezoneType
from . import alembic_utils as alembic_utils
from .database import *
from .enums import PrivacyType
from .models import Base, Guild, SandpiperMeta, User

logger = logging.getLogger(__name__)

T_Sessionmaker = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class DatabaseSQLite(Database):

    _connected: bool = False
    _engine: Optional[AsyncEngine] = None
    _session_maker: Optional[T_Sessionmaker] = None
    db_path: Union[str, Path]
    bot_user_id: Optional[int] = None

    def __init__(self, db_path: Union[str, Path]):
        if isinstance(db_path, Path):
            db_path = db_path.absolute()
        self.db_path = db_path
        self._ready_fut = None

    async def connect(self):
        logger.info(f"Connecting to database (path={self.db_path})")
        if self._connected:
            raise RuntimeError("Database is already connected")
        self._connected = True

        loop = asyncio.get_event_loop()
        # Let dependents await until ready
        self._ready_fut = loop.create_future()

        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}", echo=False, future=True
        )
        self._session_maker = cast(
            T_Sessionmaker,
            sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession),
        )

        await self._do_upgrades()

        self._ready_fut.set_result(None)

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

    async def ready(self):
        if self._ready_fut is not None:
            await self._ready_fut

    async def _do_upgrades(self):
        revision = await alembic_utils.get_current_heads(self._engine)
        if revision:
            logger.info("Performing Alembic upgrade to head (may be a no-op)")
            await alembic_utils.upgrade(self._engine, "head")
            return

        logger.info("Database has no Alembic version")
        async with self._engine.begin() as conn:
            # Check the sqlite meta table for table definitions
            conn: AsyncConnection
            no_tables = (
                await conn.execute(sa.text("SELECT 1 FROM sqlite_master LIMIT 1"))
            ).first() is None
            user_data_table_exists = (
                await conn.execute(
                    sa.text(
                        "SELECT 1 FROM sqlite_master WHERE name = 'user_data' LIMIT 1"
                    )
                )
            ).first() is not None

        if no_tables:
            # This database is empty, we can create all and stamp as head
            logger.info("Empty database; creating all and stamping as Alembic head")
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await alembic_utils.stamp(self._engine, "head")

        elif user_data_table_exists:
            # The database already existed but was not tracked yet by Alembic.
            # This means the database is aligned with the init migration.
            # Stamp it as such so we can then apply migrations to it.
            logger.info(
                "user_data table found; stamping with the appropriate "
                "Alembic revision to continue with upgrades"
            )
            await alembic_utils.stamp(self._engine, "91e18fdd475a")
            logger.info("Upgrading to head")
            await alembic_utils.upgrade(self._engine, "head")

        else:
            err_msg = (
                "Database is in an unexpected state. There appears to be "
                "data in it but it is untracked by Alembic and it cannot "
                "be automatically handled. You may have to manually stamp "
                "the Alembic revision."
            )
            logger.fatal(err_msg)
            raise RuntimeError(err_msg)

        logger.info("Upgrade complete")

    # region Helper methods

    @staticmethod
    async def _get_sandpiper_meta(session: AsyncSession) -> SandpiperMeta:
        try:
            return (
                await session.execute(
                    sa.select(SandpiperMeta).where(SandpiperMeta.id == 0)
                )
            ).scalar_one()
        except NoResultFound:
            sandpiper_meta = SandpiperMeta(id=0)
            session.add(sandpiper_meta)
            return sandpiper_meta

    @staticmethod
    async def _get_user(
        session: AsyncSession, user_id: int, create_if_missing=True
    ) -> Optional[User]:
        try:
            return (
                await session.execute(sa.select(User).where(User.user_id == user_id))
            ).scalar_one()
        except NoResultFound:
            if not create_if_missing:
                return None
            user = User(user_id=user_id)
            session.add(user)
            return user

    @staticmethod
    async def _get_guild(session: AsyncSession, guild_id: int) -> Guild:
        try:
            return (
                await session.execute(
                    sa.select(Guild).where(Guild.guild_id == guild_id)
                )
            ).scalar_one()
        except NoResultFound:
            guild = Guild(guild_id=guild_id)
            session.add(guild)
            return guild

    async def _get_user_field(self, field_name: str, user_id: int) -> Optional[Any]:
        logger.info(f"Getting {field_name} (user_id={user_id})")
        async with self._session_maker() as session, session.begin():
            try:
                return (
                    await session.execute(
                        sa.select(getattr(User, field_name)).where(
                            User.user_id == user_id
                        )
                    )
                ).scalar_one()
            except NoResultFound:
                raise UserNotInDatabase

    async def _set_user_field(self, field_name: str, user_id: int, value: Any):
        logger.info(f"Setting {field_name} (user_id={user_id}, new_value={value})")
        async with self._session_maker() as session, session.begin():
            if value is None:
                # When using the delete command, it sends None. We don't want
                # to create a new user if they're just trying to delete data
                user = await self._get_user(session, user_id, create_if_missing=False)
                if user is None:
                    raise UserNotInDatabase
            else:
                user = await self._get_user(session, user_id)
            setattr(user, field_name, value)

    async def _get_user_privacy_field(
        self, field_name: str, user_id: int
    ) -> Optional[PrivacyType]:
        logger.info(f"Getting {field_name} privacy (user_id={user_id})")
        async with self._session_maker() as session, session.begin():
            privacy = (
                await session.execute(
                    sa.select(getattr(User, f"privacy_{field_name}")).where(
                        User.user_id == user_id
                    )
                )
            ).scalar()
            return PrivacyType(privacy) if privacy is not None else None

    async def _set_user_privacy_field(
        self, field_name: str, user_id: int, new_privacy: PrivacyType
    ):
        logger.info(
            f"Setting {field_name} privacy (user_id={user_id} "
            f"new_value={new_privacy})"
        )
        async with self._session_maker() as session, session.begin():
            user = await self._get_user(session, user_id)
            setattr(user, f"privacy_{field_name}", new_privacy)

    # endregion
    # region Sandpiper meta

    async def get_sandpiper_version(self) -> str:
        logger.info("Getting Sandpiper version")
        async with self._session_maker() as session, session.begin():
            return (
                await session.execute(
                    sa.select(SandpiperMeta.version).where(SandpiperMeta.id == 0)
                )
            ).scalar()

    async def set_sandpiper_version(self, new_version: str):
        logger.info(f"Setting Sandpiper version (new_value={new_version})")
        async with self._session_maker() as session, session.begin():
            sandpiper_meta = await self._get_sandpiper_meta(session)
            sandpiper_meta.version = new_version

    # endregion
    # region Full user

    async def create_user(self, user_id: int):
        logger.info(f"Creating user (user_id={user_id})")
        async with self._session_maker() as session, session.begin():
            user = User(user_id=user_id)
            session.add(user)

    async def delete_user(self, user_id: int):
        logger.info(f"Deleting user (user_id={user_id})")
        async with self._session_maker() as session, session.begin():
            await session.execute(sa.delete(User).where(User.user_id == user_id))

    async def get_all_user_ids(self) -> list[int]:
        logger.info("Getting all user IDs")
        async with self._session_maker() as session, session.begin():
            return (await session.execute(sa.select(User.user_id))).scalars().all()

    # endregion
    # region Preferred name

    async def get_preferred_name(self, user_id: int) -> Optional[str]:
        return await self._get_user_field("preferred_name", user_id)

    async def set_preferred_name(self, user_id: int, new_preferred_name: Optional[str]):
        await self._set_user_field("preferred_name", user_id, new_preferred_name)

    async def get_privacy_preferred_name(self, user_id: int) -> Optional[PrivacyType]:
        return await self._get_user_privacy_field("preferred_name", user_id)

    async def set_privacy_preferred_name(self, user_id: int, new_privacy: PrivacyType):
        await self._set_user_privacy_field("preferred_name", user_id, new_privacy)

    async def find_users_by_preferred_name(self, name: str) -> list[tuple[int, str]]:
        logger.info(f"Finding users by preferred name (name={name})")
        if name == "":
            logger.info("Skipping empty string")
            return []

        async with self._session_maker() as session, session.begin():
            return (
                await session.execute(
                    sa.select(User.user_id, User.preferred_name)
                    .where(User.preferred_name.like(f"%{name}%"))
                    .where(User.privacy_preferred_name == PrivacyType.PUBLIC)
                )
            ).all()

    # endregion
    # region Pronouns

    async def get_pronouns(self, user_id: int) -> Optional[str]:
        return await self._get_user_field("pronouns", user_id)

    async def set_pronouns(self, user_id: int, new_pronouns: Optional[str]):
        await self._set_user_field("pronouns", user_id, new_pronouns)

    async def get_privacy_pronouns(self, user_id: int) -> Optional[PrivacyType]:
        return await self._get_user_privacy_field("pronouns", user_id)

    async def set_privacy_pronouns(self, user_id: int, new_privacy: PrivacyType):
        await self._set_user_privacy_field("pronouns", user_id, new_privacy)

    # endregion
    # region Birthday

    async def get_birthday(self, user_id: int) -> Optional[dt.date]:
        return await self._get_user_field("birthday", user_id)

    async def set_birthday(self, user_id: int, new_birthday: Optional[dt.date]):
        await self._set_user_field("birthday", user_id, new_birthday)

    async def get_privacy_birthday(self, user_id: int) -> Optional[PrivacyType]:
        return await self._get_user_privacy_field("birthday", user_id)

    async def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        await self._set_user_privacy_field("birthday", user_id, new_privacy)

    @staticmethod
    def _birthday_range_predicate(start: dt.date, end: dt.date):
        wrap = (32 * start.month + start.day) > (32 * end.month + end.day)

        def f(d: dt.date) -> bool:
            if wrap:
                # Start date goes forward and wraps around the year to end date
                if end.month < d.month < start.month:
                    # Between the start and end months
                    return False
            else:
                if d.month < start.month or d.month > end.month:
                    # Around the start and end months
                    return False

            if wrap and (d.month == start.month and d.month == end.month):
                # We're wrapping around and the start/end month are the same.
                # This means there will be a little sliver of exclusion within
                # this month, between the end and start day.
                if end.day < d.day < start.day:
                    return False
            else:
                # Otherwise we just need to ensure the day is greater/less than
                # the target days if this date's month equals either of the
                # bounded dates' months
                if d.month == start.month and d.day < start.day:
                    return False
                if d.month == end.month and d.day > end.day:
                    return False

            return True

        return f

    async def get_birthdays_range(
        self,
        start: dt.date,
        end: dt.date,
        max_last_notification_time: Optional[dt.date] = None,
    ) -> list[tuple[Annotated[int, "user_id"], dt.date]]:
        logger.info(
            f"Getting all birthdays between {start.day}-{start.month} and "
            f"{end.day}-{end.month}"
        )
        if not isinstance(start, dt.date) or not isinstance(end, dt.date):
            raise TypeError("start and end must be instances of datetime.date")

        async with self._session_maker() as session, session.begin():
            stmt = (
                sa.select(User.user_id, User.birthday)
                .where(User.birthday.isnot(None))
                .where(User.privacy_birthday == PrivacyType.PUBLIC)
            )
            if max_last_notification_time is not None:
                stmt = stmt.where(
                    User.last_birthday_notification.is_(None)
                    | (User.last_birthday_notification <= max_last_notification_time)
                )
            birthdays_unfiltered = (await session.execute(stmt)).all()

        return list(
            filter(
                lambda r: self._birthday_range_predicate(start, end)(r[1]),
                birthdays_unfiltered,
            )
        )

    # endregion
    # region Age

    async def get_privacy_age(self, user_id: int) -> Optional[PrivacyType]:
        return await self._get_user_privacy_field("age", user_id)

    async def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        await self._set_user_privacy_field("age", user_id, new_privacy)

    # endregion
    # region Timezone

    async def get_timezone(self, user_id: int) -> Optional[TimezoneType]:
        tz_name = await self._get_user_field("timezone", user_id)
        if tz_name:
            return pytz.timezone(tz_name)
        return None

    async def set_timezone(self, user_id: int, new_timezone: Optional[TimezoneType]):
        if new_timezone:
            new_timezone = new_timezone.zone
        await self._set_user_field("timezone", user_id, new_timezone)

    async def get_privacy_timezone(self, user_id: int) -> Optional[PrivacyType]:
        return await self._get_user_privacy_field("timezone", user_id)

    async def set_privacy_timezone(self, user_id: int, new_privacy: PrivacyType):
        await self._set_user_privacy_field("timezone", user_id, new_privacy)

    async def get_all_timezones(self) -> list[tuple[int, TimezoneType]]:
        logger.info("Getting all user timezones")
        async with self._session_maker() as session, session.begin():
            stmt = (
                sa.select(User.user_id, User.timezone)
                .where(User.timezone.isnot(None))
                .where(User.privacy_timezone == PrivacyType.PUBLIC)
            )
            if self.bot_user_id:
                stmt = stmt.where(User.user_id != self.bot_user_id)
            result = (await session.execute(stmt)).all()
        return [(uid, pytz.timezone(tz_name)) for uid, tz_name in result]

    # endregion
    # region Other user stuff

    async def get_last_birthday_notification(self, user_id: int) -> dt.datetime:
        return await self._get_user_field("last_birthday_notification", user_id)

    async def set_last_birthday_notification(self, user_id: int, new_date: dt.datetime):
        await self._set_user_field("last_birthday_notification", user_id, new_date)

    # endregion
    # region Guilds

    async def get_guild_birthday_channel(self, guild_id: int) -> Optional[str]:
        logger.info(f"Getting guild birthday_channel (guild_id={guild_id})")
        async with self._session_maker() as session, session.begin():
            return (
                await session.execute(
                    sa.select(Guild.birthday_channel).where(Guild.guild_id == guild_id)
                )
            ).scalar()

    async def set_guild_birthday_channel(
        self, guild_id: int, new_birthday_channel: Optional[int]
    ):
        logger.info(
            f"Setting guild birthday_channel (guild_id={guild_id}, "
            f"new_value={new_birthday_channel})"
        )
        async with self._session_maker() as session, session.begin():
            guild = await self._get_guild(session, guild_id)
            guild.birthday_channel = new_birthday_channel

    # endregion
