from abc import ABCMeta, abstractmethod
import datetime
from typing import List, Optional, Tuple

from ..common.time import TimezoneType
from .enums import PrivacyType

DEFAULT_PRIVACY = PrivacyType.PRIVATE


class DatabaseError(Exception):
    pass


class Database(metaclass=ABCMeta):

    @abstractmethod
    async def create_table(self):
        pass

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
    async def find_users_by_preferred_name(self, name: str) -> List[Tuple[int, str]]:
        pass

    @abstractmethod
    async def get_all_timezones(self) -> List[Tuple[int, TimezoneType]]:
        pass

    @abstractmethod
    async def delete_user(self, user_id: int):
        pass

    @abstractmethod
    async def get_preferred_name(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_preferred_name(self, user_id: int, new_preferred_name: Optional[str]):
        pass

    @abstractmethod
    async def get_privacy_preferred_name(self, user_id: int) -> PrivacyType:
        pass

    @abstractmethod
    async def set_privacy_preferred_name(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    async def get_pronouns(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    async def set_pronouns(self, user_id: int, new_pronouns: Optional[str]):
        pass

    @abstractmethod
    async def get_privacy_pronouns(self, user_id: int) -> PrivacyType:
        pass

    @abstractmethod
    async def set_privacy_pronouns(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    async def get_birthday(self, user_id: int) -> Optional[datetime.date]:
        pass

    @abstractmethod
    async def set_birthday(self, user_id: int, new_birthday: Optional[datetime.date]):
        pass

    @abstractmethod
    async def get_privacy_birthday(self, user_id: int) -> PrivacyType:
        pass

    @abstractmethod
    async def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    async def get_timezone(self, user_id: int) -> Optional[TimezoneType]:
        pass

    @abstractmethod
    async def set_timezone(self, user_id: int,
                           new_timezone: Optional[TimezoneType]):
        pass

    @abstractmethod
    async def get_privacy_timezone(self, user_id: int) -> PrivacyType:
        pass

    @abstractmethod
    async def set_privacy_timezone(self, user_id: int, new_privacy: PrivacyType):
        pass

    @staticmethod
    def _calculate_age(birthday: datetime.date, on_day: datetime.date):
        birthday_this_year = datetime.date(on_day.year, birthday.month,
                                           birthday.day)
        age = on_day.year - birthday.year
        if on_day < birthday_this_year:
            return age - 1
        return age

    async def get_age(self, user_id: int) -> Optional[int]:
        birthday = await self.get_birthday(user_id)
        if birthday is None:
            return None
        return self._calculate_age(birthday, datetime.date.today())

    @abstractmethod
    async def get_privacy_age(self, user_id: int) -> PrivacyType:
        pass

    @abstractmethod
    async def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        pass
