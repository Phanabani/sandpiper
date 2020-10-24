import datetime
import logging
from pathlib import Path
import sqlite3
from typing import Any, List, NoReturn, Optional, Tuple, Union

import pytz

from .database import *
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
        logger.info(f'Connecting to database (path={self.db_path})')
        self._con = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def disconnect(self):
        logger.info(f'Disconnecting from database (path={self.db_path})')
        self._con.close()
        self._con = None

    def connected(self):
        return self._con is not None

    def create_table(self):
        logger.info('Creating user_info table if not exists')
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
        logger.info('Creating indices for user_info table if not exist')
        stmt = '''
            CREATE INDEX IF NOT EXISTS index_users_preferred_name
            ON user_info(preferred_name)
        '''
        try:
            with self._con:
                self._con.execute(stmt)
        except sqlite3.Error:
            logger.error('Failed to create indices', exc_info=True)

    def find_users_by_preferred_name(self, name: str) -> List[Tuple[int, str]]:
        logger.info(f'Finding users by preferred name (name={name!r})')
        stmt = '''
            SELECT user_id, preferred_name FROM user_info
            WHERE preferred_name like :name
                AND privacy_preferred_name = :privacy
        '''
        args = {'name': f'%{name}%', 'privacy': PrivacyType.PUBLIC}
        try:
            with self._con:
                return self._con.execute(stmt, args).fetchall()
        except sqlite3.Error:
            logger.error('Failed to find users by name', exc_info=True)

    def delete_user(self, user_id: int):
        logger.info(f'Deleting user (user_id={user_id})')
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
        logger.info(f'Getting data from column {col_name} (user_id={user_id})')
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
        logger.info(f'Setting data in column {col_name} (user_id={user_id} '
                    f'new_value={new_value!r})')
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

    def set_preferred_name(self, user_id: int,
                           new_preferred_name: Optional[str]):
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

    def set_pronouns(self, user_id: int, new_pronouns: Optional[str]):
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

    def set_birthday(self, user_id: int, new_birthday: Optional[datetime.date]):
        self._do_execute_set('birthday', user_id, new_birthday)

    def get_privacy_birthday(self, user_id: int) -> PrivacyType:
        privacy = self._do_execute_get('privacy_birthday', user_id,
                                       DEFAULT_PRIVACY)
        return PrivacyType(privacy)

    def set_privacy_birthday(self, user_id: int, new_privacy: PrivacyType):
        self._do_execute_set('privacy_birthday', user_id, new_privacy)

    # Timezone

    def get_timezone(self, user_id: int) -> Optional[TimezoneType]:
        timezone_name = self._do_execute_get('timezone', user_id)
        if timezone_name:
            return pytz.timezone(timezone_name)
        return None

    def set_timezone(self, user_id: int,
                     new_timezone: Optional[TimezoneType]):
        if new_timezone:
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
