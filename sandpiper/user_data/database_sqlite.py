import datetime
from pathlib import Path
import sqlite3
from typing import NoReturn, Union

import pytz

from .database import Database
from .enums import PrivacyType
from .errors import PrivacyError


# https://docs.python.org/3.8/library/sqlite3.html#converting-sqlite-values-to-custom-python-types
def adapt_timezone(timezone: pytz.tzinfo.BaseTzInfo) -> str:
    return timezone.zone


def convert_timezone(timezone_name: bytes) -> pytz.tzinfo.BaseTzInfo:
    return pytz.timezone(timezone_name.decode('utf_8'))


sqlite3.register_adapter(pytz.tzinfo.BaseTzInfo, adapt_timezone)
sqlite3.register_converter('timezone', convert_timezone)


class DatabaseSQLite(Database):

    def __init__(self, db_path: Union[str, Path]):
        self._con = sqlite3.connect(
            db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.create_database()

    def close(self):
        self._con.close()

    def create_database(self):
        cur = self._con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_bios (
                user_id INTEGER PRIMARY KEY, 
                preferred_name TEXT, 
                pronouns TEXT, 
                birthday DATE, 
                timezone TIMEZONE, 
                privacy_preferred_name TINYINT, 
                privacy_pronouns TINYINT, 
                privacy_birthday TINYINT, 
                privacy_timezone TINYINT
            )
            """
        )

    def test_privacy(self, field: str, user_id: int) -> NoReturn:
        cur = self._con.cursor()
        cur.execute(
            f'SELECT privacy_{field} FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        privacy: PrivacyType = cur.fetchone()[0]
        if privacy == PrivacyType.PRIVATE:
            raise PrivacyError()

    def get_preferred_name(self, user_id: int) -> str:
        self.test_privacy('preferred_name', user_id)
        cur = self._con.cursor()
        cur.execute(
            'SELECT preferred_name FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_preferred_name(self, user_id: int, new_preferred_name: str):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (preferred_name) VALUES (?)
            ''',
            (new_preferred_name,)
        )

    def get_pronouns(self, user_id: int) -> str:
        self.test_privacy('pronouns', user_id)
        cur = self._con.cursor()
        cur.execute(
            'SELECT pronouns FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_pronouns(self, user_id: int, new_pronouns: str):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (pronouns) VALUES (?)
            ''',
            (new_pronouns,)
        )

    def get_birthday(self, user_id: int) -> datetime.date:
        self.test_privacy('birthday', user_id)
        cur = self._con.cursor()
        cur.execute(
            'SELECT birthday FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_birthday(self, user_id: int, new_birthday: datetime.date):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (birthday) VALUES (?)
            ''',
            (new_birthday,)
        )

    def get_timezone(self, user_id: int) -> pytz.tzinfo.BaseTzInfo:
        self.test_privacy('timezone', user_id)
        cur = self._con.cursor()
        cur.execute(
            'SELECT timezone FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_timezone(self, user_id: int, new_timezone: pytz.tzinfo.BaseTzInfo):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (timezone) VALUES (?)
            ''',
            (new_timezone,)
        )
