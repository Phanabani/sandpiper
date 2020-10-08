import datetime
from pathlib import Path
import sqlite3
from typing import Optional, Union

import pytz

from .database import Database
from .enums import PrivacyType

__all__ = ['DatabaseSQLite']

DEFAULT_PRIVACY = PrivacyType.PRIVATE


# https://docs.python.org/3.8/library/sqlite3.html#converting-sqlite-values-to-custom-python-types
def adapt_timezone(timezone: pytz.tzinfo.BaseTzInfo) -> str:
    return timezone.zone


def convert_timezone(timezone_name: bytes) -> pytz.tzinfo.BaseTzInfo:
    return pytz.timezone(timezone_name.decode('utf_8'))


sqlite3.register_adapter(pytz.tzinfo.BaseTzInfo, adapt_timezone)
sqlite3.register_converter('timezone', convert_timezone)


class DatabaseSQLite(Database):

    _con: Optional[sqlite3.Connection] = None
    _cur: Optional[sqlite3.Cursor] = None
    db_path: Union[str, Path]

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        self.connect()
        self.create_table()

    def connect(self):
        self._con = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self._cur = self._con.cursor()

    def disconnect(self):
        self._con.close()
        self._con = None
        self._cur = None

    def connected(self):
        return self._con is not None

    def create_table(self):
        self._cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_info (
                user_id INTEGER PRIMARY KEY, 
                preferred_name TEXT, 
                pronouns TEXT, 
                birthday DATE, 
                timezone TIMEZONE, 
                privacy_preferred_name TINYINT, 
                privacy_pronouns TINYINT, 
                privacy_birthday TINYINT, 
                privacy_age TINYINT, 
                privacy_timezone TINYINT
            )
            """
        )

    def clear_data(self, user_id: int):
        self._cur.execute(
            'DELETE FROM user_info WHERE user_id = ?',
            (user_id,)
        )

    # Preferred name

    def get_preferred_name(self, user_id: int) -> Optional[str]:
        stmt = 'SELECT preferred_name FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return None
        return result[0]

    def set_preferred_name(self, user_id: int, new_preferred_name: str):
        stmt = 'REPLACE INTO user_info (preferred_name) VALUES (?)'
        self._cur.execute(stmt, (new_preferred_name,))

    def get_privacy_preferred_name(self, user_id: int) -> int:
        stmt = 'SELECT privacy_preferred_name FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return DEFAULT_PRIVACY
        return result[0]

    def set_privacy_preferred_name(self, user_id: int, new_privacy: PrivacyType):
        stmt = 'REPLACE INTO user_info (privacy_preferred_name) VALUES (?)'
        self._cur.execute(stmt, (new_privacy,))

    # Pronouns

    def get_pronouns(self, user_id: int) -> Optional[str]:
        stmt = 'SELECT pronouns FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return None
        return result[0]

    def set_pronouns(self, user_id: int, new_pronouns: str):
        stmt = 'REPLACE INTO user_info (pronouns) VALUES (?)'
        self._cur.execute(stmt, (new_pronouns,))

    def get_privacy_pronouns(self, user_id: int) -> int:
        stmt = 'SELECT privacy_pronouns FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return DEFAULT_PRIVACY
        return result[0]

    def set_privacy_pronouns(self, user_id: int, new_privacy: PrivacyType):
        stmt = 'REPLACE INTO user_info (privacy_pronouns) VALUES (?)'
        self._cur.execute(stmt, (new_privacy,))

    # Birthday

    def get_birthday(self, user_id: int) -> Optional[datetime.date]:
        stmt = 'SELECT birthday FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return None
        return result[0]

    def set_birthday(self, user_id: int, new_birthday: datetime.date):
        stmt = 'REPLACE INTO user_info (birthday) VALUES (?)'
        self._cur.execute(stmt, (new_birthday,))

    def get_privacy_birthday(self, user_id: int) -> int:
        stmt = 'SELECT privacy_birthday FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return DEFAULT_PRIVACY
        return result[0]

    def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        stmt = 'REPLACE INTO user_info (privacy_birthday) VALUES (?)'
        self._cur.execute(stmt, (new_privacy,))

    # Timezone

    def get_timezone(self, user_id: int) -> Optional[pytz.tzinfo.BaseTzInfo]:
        stmt = 'SELECT timezone FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return None
        return result[0]

    def set_timezone(self, user_id: int, new_timezone: pytz.tzinfo.BaseTzInfo):
        stmt = 'REPLACE INTO user_info (timezone) VALUES (?)'
        self._cur.execute(stmt, (new_timezone,))

    def get_privacy_timezone(self, user_id: int) -> int:
        stmt = 'SELECT privacy_timezone FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return DEFAULT_PRIVACY
        return result[0]

    def set_privacy_timezone(self, user_id: int, new_privacy: PrivacyType):
        stmt = 'REPLACE INTO user_info (privacy_timezone) VALUES (?)'
        self._cur.execute(stmt, (new_privacy,))

    # Age

    def get_privacy_age(self, user_id: int) -> int:
        stmt = 'SELECT privacy_age FROM user_info WHERE user_id = ?'
        result = self._cur.execute(stmt, (user_id,)).fetchone()
        if result is None:
            return DEFAULT_PRIVACY
        return result[0]

    def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        stmt = 'REPLACE INTO user_info (privacy_age) VALUES (?)'
        self._cur.execute(stmt, (new_privacy,))
