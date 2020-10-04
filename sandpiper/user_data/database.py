from abc import ABCMeta, abstractmethod
from datetime import datetime

from pytz import timezone


class Database(metaclass=ABCMeta):

    @abstractmethod
    def create_database(self):
        pass

    @abstractmethod
    def get_preferred_name(self, user_id: int) -> str:
        pass

    @abstractmethod
    def set_preferred_name(self, user_id: int, new_name: str):
        pass

    @abstractmethod
    def get_pronouns(self, user_id: int) -> str:
        pass

    @abstractmethod
    def set_pronouns(self, user_id: int, new_pronouns: str):
        pass

    @abstractmethod
    def get_birthday(self, user_id: int) -> datetime:
        pass

    @abstractmethod
    def set_birthday(self, user_id: int, new_birthday: datetime):
        pass

    @abstractmethod
    def get_timezone(self, user_id: int) -> timezone:
        pass

    @abstractmethod
    def set_timezone(self, user_id: int, new_timezone: timezone):
        pass
