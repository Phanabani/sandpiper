import datetime
import logging
from pathlib import Path
import sqlite3
from typing import Any, NoReturn, Optional, Union

import pytz

from .database import Database, DatabaseError
from .enums import PrivacyType

__all__ = ['DatabaseSQLite']

logger = logging.getLogger('sandpiper.user_data.database_sqlite')

DEFAULT_PRIVACY = PrivacyType.PRIVATE


class DatabaseSQLite(Database):

    _con: Optional[sqlite3.Connection] = None
    db_path: Union[str, Path]

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = db_path
        self.connect()
        self.create_table()

    def connect(self):
        self._con = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def disconnect(self):
        self._con.close()
        self._con = None

    def connected(self):
        return self._con is not None

    def create_table(self):
        stmt = '''
            CREATE TABLE IF NOT EXISTS user_info (
                user_id INTEGER PRIMARY KEY UNIQUE, 
                preferred_name TEXT, 
                pronouns TEXT, 
                birthday DATE, 
                timezone TEXT, 
                privacy_preferred_name TINYINT, 
                privacy_pronouns TINYINT, 
                privacy_birthday TINYINT, 
                privacy_age TINYINT, 
                privacy_timezone TINYINT
            )
        '''
        try:
            with self._con:
                self._con.execute(stmt)
        except sqlite3.Error:
            logger.error('Failed to create table', exc_info=True)
        self.create_indices()

    def create_indices(self):
        stmt = '''
            CREATE INDEX IF NOT EXISTS index_users_preferred_name
            ON user_info(preferred_name)
        '''
        try:
            with self._con:
                self._con.execute(stmt)
        except sqlite3.Error:
            logger.error('Failed to create indices', exc_info=True)

    def delete_user(self, user_id: int):
        stmt = 'DELETE FROM user_info WHERE user_id = ?'
        args = (user_id,)
        try:
            with self._con:
                self._con.execute(stmt, args)
        except sqlite3.Error:
            logger.error(f'Failed to delete row (user_id={user_id})',
                         exc_info=True)
            raise DatabaseError('Failed to delete user data')

    # Getter/setter helpers

    def _do_execute_get(self, col_name: str, user_id: int,
                        default: Any = None) -> Optional[Any]:
        stmt = f'SELECT {col_name} FROM user_info WHERE user_id = ?'
        try:
            with self._con:
                result = self._con.execute(stmt, (user_id,)).fetchone()
        except sqlite3.Error:
            logger.error(
                f'Failed to get value (column={col_name!r} user_id={user_id})',
                exc_info=True)
            raise DatabaseError('Failed to get value')
        if result is None or result[0] is None:
            return default
        return result[0]

    def _do_execute_set(self, col_name: str, user_id: int,
                        new_value: Any) -> NoReturn:
        stmt = f'''
            INSERT INTO user_info(user_id, {col_name})
            VALUES (:user_id, :new_value)
            ON CONFLICT (user_id) DO
            UPDATE SET {col_name} = :new_value
        '''
        args = {'user_id': user_id, 'new_value': new_value}
        try:
            with self._con:
                self._con.execute(stmt, args)
        except sqlite3.Error:
            logger.error(f'Failed to set value (column={col_name!r} '
                         f'user_id={user_id} new_value={new_value!r})',
                         exc_info=True)
            raise DatabaseError('Failed to set value')

    # Preferred name

    def get_preferred_name(self, user_id: int) -> Optional[str]:
        return self._do_execute_get('preferred_name', user_id)

    def set_preferred_name(self, user_id: int, new_preferred_name: str):
        self._do_execute_set('preferred_name', user_id, new_preferred_name)

    def get_privacy_preferred_name(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_preferred_name', user_id,
                                       DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_preferred_name(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_preferred_name', user_id, new_privacy)

    # Pronouns

    def get_pronouns(self, user_id: int) -> Optional[str]:
        return self._do_execute_get('pronouns', user_id)

    def set_pronouns(self, user_id: int, new_pronouns: str):
        self._do_execute_set('pronouns', user_id, new_pronouns)

    def get_privacy_pronouns(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_pronouns', user_id,
                                       DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_pronouns(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_pronouns', user_id, new_privacy)

    # Birthday

    def get_birthday(self, user_id: int) -> Optional[datetime.date]:
        return self._do_execute_get('birthday', user_id)

    def set_birthday(self, user_id: int, new_birthday: datetime.date):
        self._do_execute_set('birthday', user_id, new_birthday)

    def get_privacy_birthday(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_birthday', user_id,
                                       DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_birthday', user_id, new_privacy)

    # Timezone

    def get_timezone(self, user_id: int) -> Optional[pytz.tzinfo.BaseTzInfo]:
        timezone_name = self._do_execute_get('timezone', user_id)
        if timezone_name:
            return pytz.timezone(timezone_name)
        return None

    def set_timezone(self, user_id: int, new_timezone: pytz.tzinfo.BaseTzInfo):
        new_timezone = new_timezone.zone
        self._do_execute_set('timezone', user_id, new_timezone)

    def get_privacy_timezone(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_timezone', user_id,
                                       DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_timezone(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_timezone', user_id, new_privacy)

    # Age

    def get_privacy_age(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_age', user_id, DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_age(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_age', user_id, new_privacy)
