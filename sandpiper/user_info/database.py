from abc import ABCMeta, abstractmethod
import datetime
from typing import Optional

import pytz


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
    def get_preferred_name(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    def set_preferred_name(self, user_id: int, new_preferred_name: str):
        pass

    @abstractmethod
    def get_pronouns(self, user_id: int) -> Optional[str]:
        pass

    @abstractmethod
    def set_pronouns(self, user_id: int, new_pronouns: str):
        pass

    @abstractmethod
    def get_birthday(self, user_id: int) -> Optional[datetime.date]:
        pass

    @abstractmethod
    def set_birthday(self, user_id: int, new_birthday: datetime.date):
        pass

    @abstractmethod
    def get_timezone(self, user_id: int) -> Optional[pytz.tzinfo.BaseTzInfo]:
        pass

    @abstractmethod
    def set_timezone(self, user_id: int, new_timezone: pytz.tzinfo.BaseTzInfo):
        pass
