from abc import ABCMeta, abstractmethod
import datetime as dt
from typing import Annotated, Optional

import pytz

from .enums import PrivacyType
from .pronouns import Pronouns
from sandpiper.common.time import TimezoneType, utc_now

__all__ = (
    'DEFAULT_PRIVACY',
    'Database', 'DatabaseError',
)

DEFAULT_PRIVACY = PrivacyType.PRIVATE


class DatabaseError(Exception):
    pass


class Database(metaclass=ABCMeta):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def connected(self) -> bool:
        pass

    @abstractmethod
    async def ready(self):
        """Awaits until the database is ready"""
        pass

    # region Full user

    @abstractmethod
    async def create_user(self, user_id: int):
        pass

    @abstractmethod
    async def delete_user(self, user_id: int):
        pass

    # endregion
    # region Name

    @abstractmethod
    async def get_preferred_name(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_preferred_name(
            self, user_id: int, new_preferred_name: Optional[str]
    ):
        pass

    @abstractmethod
    async def get_privacy_preferred_name(
            self, user_id: int
    ) -> Optional[PrivacyType]:
        pass

    @abstractmethod
    async def set_privacy_preferred_name(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    @abstractmethod
    async def find_users_by_preferred_name(
            self, name: str
    ) -> list[tuple[int, str]]:
        pass

    # endregion
    # region Pronouns

    @abstractmethod
    async def get_pronouns(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_pronouns(self, user_id: int, new_pronouns: Optional[str]):
        pass

    @abstractmethod
    async def get_privacy_pronouns(self, user_id: int) -> Optional[PrivacyType]:
        pass

    @abstractmethod
    async def set_privacy_pronouns(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    async def get_pronouns_parsed(self, user_id: int) -> list[Pronouns]:
        pronouns = await self.get_pronouns(user_id)
        if pronouns is None:
            return []
        return Pronouns.parse(pronouns)

    # endregion
    # region Birthday

    @abstractmethod
    async def get_birthday(self, user_id: int) -> Optional[dt.date]:
        pass

    @abstractmethod
    async def set_birthday(
            self, user_id: int, new_birthday: Optional[dt.date]
    ):
        pass

    @abstractmethod
    async def get_privacy_birthday(self, user_id: int) -> Optional[PrivacyType]:
        pass

    @abstractmethod
    async def set_privacy_birthday(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    @abstractmethod
    async def get_birthdays_range(
            self, start: dt.date, end: dt.date,
            only_if_notification_not_sent: bool = False
    ) -> list[tuple[Annotated[int, 'user_id'], dt.date]]:
        """
        Get a list of (user_id, birthday) for all users with birthdays between
        `start` and `end`, inclusive. If `start` is later than `end`, the check
        will wrap around the new year (e.g. start=December, end=February will
        get birthdays in December, January, and February).

        :param start: the earliest date to filter for birthdays
        :param end: the latest date to filter for birthdays
        :param only_if_notification_not_sent: only select data for users with
            birthday_notification_sent == False. This is to make birthday
            notifications atomic.
        :return: a list of (user_id, birthday)
        """
        pass

    # endregion
    # region Age

    @staticmethod
    def _calculate_age(
            birthday: dt.date, tz: TimezoneType, at_time: dt.datetime
    ):
        # The user's birthday in `at_time`'s year at midnight (localized to
        # their timezone)
        birthday_this_year = tz.localize(dt.datetime(
            at_time.year, birthday.month, birthday.day, 0, 0
        ))
        year_diff = at_time.year - birthday.year
        if at_time < birthday_this_year:
            # They haven't reached their birthday for this year
            return year_diff - 1
        return year_diff

    async def get_age(self, user_id: int) -> Optional[int]:
        birthday = await self.get_birthday(user_id)
        if birthday is None:
            return None
        if birthday.year == 1:
            # Birthdays with year == 1 are considered yearless since year can't
            # be None
            return None

        tz = await self.get_timezone(user_id)
        if tz is None:
            tz = pytz.UTC

        return self._calculate_age(birthday, tz, utc_now())

    @abstractmethod
    async def get_privacy_age(self, user_id: int) -> Optional[PrivacyType]:
        pass

    @abstractmethod
    async def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        pass

    # endregion
    # region Timezone

    @abstractmethod
    async def get_timezone(self, user_id: int) -> Optional[TimezoneType]:
        pass

    @abstractmethod
    async def set_timezone(
            self, user_id: int, new_timezone: Optional[TimezoneType]
    ):
        pass

    @abstractmethod
    async def get_privacy_timezone(self, user_id: int) -> Optional[PrivacyType]:
        pass

    @abstractmethod
    async def set_privacy_timezone(
            self, user_id: int, new_privacy: PrivacyType
    ):
        pass

    @abstractmethod
    async def get_all_timezones(self) -> list[tuple[int, TimezoneType]]:
        pass

    # endregion
    # region Other user stuff

    @abstractmethod
    async def get_birthday_notification_sent(self, user_id: int) -> bool:
        pass

    @abstractmethod
    async def set_birthday_notification_sent(
            self, user_id: int, new_value: bool
    ):
        pass

    # endregion
    # region Guild settings

    @abstractmethod
    async def get_guild_birthday_channel(
            self, guild_id: int
    ) -> Optional[int]:
        pass

    @abstractmethod
    async def set_guild_birthday_channel(
            self, guild_id: int, new_birthday_channel: Optional[int]
    ):
        pass

    # endregion
