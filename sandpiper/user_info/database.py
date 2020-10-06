from abc import ABCMeta, abstractmethod
import datetime
from typing import Optional

import pytz

from .enums import PrivacyType


class Database(metaclass=ABCMeta):

    @abstractmethod
    def create_database(self):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def connected(self) -> bool:
        pass

    @abstractmethod
    def clear_data(self, user_id: int):
        pass

    @abstractmethod
    def get_preferred_name(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    def set_preferred_name(self, user_id: int, new_preferred_name: str):
        pass

    @abstractmethod
    def get_privacy_preferred_name(self, user_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def set_privacy_preferred_name(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    def get_pronouns(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    def set_pronouns(self, user_id: int, new_pronouns: str):
        pass

    @abstractmethod
    def get_privacy_pronouns(self, user_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def set_privacy_pronouns(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    def get_birthday(self, user_id: int) -> Optional[datetime.date]:
        pass

    @abstractmethod
    def set_birthday(self, user_id: int, new_birthday: datetime.date):
        pass

    @abstractmethod
    def get_privacy_birthday(self, user_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        pass

    @abstractmethod
    def get_timezone(self, user_id: int) -> Optional[pytz.tzinfo.BaseTzInfo]:
        pass

    @abstractmethod
    def set_timezone(self, user_id: int, new_timezone: pytz.tzinfo.BaseTzInfo):
        pass

    @abstractmethod
    def get_privacy_timezone(self, user_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def set_privacy_timezone(self, user_id: int, new_privacy: PrivacyType):
        pass

    @staticmethod
    def _calculate_age(birthday: datetime.date, on_day: datetime.date):
        birthday_this_year = datetime.date(on_day.year, birthday.month,
                                           birthday.day)
        age = on_day.year - birthday.year
        if on_day < birthday_this_year:
            return age - 1
        return age

    def get_age(self, user_id: int) -> Optional[int]:
        birthday = self.get_birthday(user_id)
        if birthday is None:
            return None
        return self._calculate_age(birthday, datetime.date.today())

    @abstractmethod
    def get_privacy_age(self, user_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        pass
