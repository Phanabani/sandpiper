from datetime import datetime
from pathlib import Path
import sqlite3
from typing import NoReturn, Union

from pytz import timezone

from .database import Database
from .enums import PrivacyType
from .errors import PrivacyError


class DatabaseSQLite(Database):

    def __init__(self, db_path: Union[str, Path]):
        self._con = sqlite3.connect(db_path)
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
                timezone TEXT, 
                privacy_preferred_name TINYINT, 
                privacy_pronouns TINYINT, 
                privacy_birthday TINYINT, 
                privacy_timezone TINYINT
            )
            """
        )

    def test_privacy(self, user_id: int, field: str) -> NoReturn:
        cur = self._con.cursor()
        cur.execute(
            f'SELECT privacy_{field} FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        privacy: PrivacyType = cur.fetchone()[0]
        if privacy == PrivacyType.PRIVATE:
            raise PrivacyError()

    def get_preferred_name(self, user_id: int) -> str:
        self.test_privacy(user_id, 'preferred_name')
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
        self.test_privacy(user_id, 'pronouns')
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

    def get_birthday(self, user_id: int) -> datetime:
        self.test_privacy(user_id, 'birthday')
        cur = self._con.cursor()
        cur.execute(
            'SELECT birthday FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_birthday(self, user_id: int, new_birthday: datetime):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (birthday) VALUES (?)
            ''',
            (new_birthday,)
        )

    def get_timezone(self, user_id: int) -> timezone:
        self.test_privacy(user_id, 'timezone')
        cur = self._con.cursor()
        cur.execute(
            'SELECT timezone FROM user_bios WHERE user_id = ?',
            (user_id,)
        )
        return cur.fetchone()[0]

    def set_timezone(self, user_id: int, new_timezone: timezone):
        cur = self._con.cursor()
        cur.execute(
            '''
            INSERT OR REPLACE INTO user_bios
            (timezone) VALUES (?)
            ''',
            (new_timezone,)
        )
