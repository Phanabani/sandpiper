import datetime as dt
import unittest

import pytz

from sandpiper.user_data.database_sqlite import DatabaseSQLite
from sandpiper.user_data.enums import PrivacyType

__all__ = ['TestDatabaseConnection', 'TestDatabase']

CONNECTION = ':memory:'


class TestDatabaseConnection(unittest.IsolatedAsyncioTestCase):

    async def test_connection(self):
        db = DatabaseSQLite(CONNECTION)
        await db.connect()
        self.assertTrue(await db.connected())
        await db.disconnect()
        self.assertFalse(await db.connected())


class TestDatabase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self._db = DatabaseSQLite(CONNECTION)
        await self._db.connect()

    async def asyncTearDown(self) -> None:
        await self._db.disconnect()

    async def test_privacy(self):
        db = self._db
        user_id = 123

        # Nonexistent user
        async def assert_all_privacies(privacy: PrivacyType):
            self.assertIs(await db.get_privacy_preferred_name(user_id), privacy)
            self.assertIs(await db.get_privacy_pronouns(user_id), privacy)
            self.assertIs(await db.get_privacy_birthday(user_id), privacy)
            self.assertIs(await db.get_privacy_age(user_id), privacy)
            self.assertIs(await db.get_privacy_timezone(user_id), privacy)

        # Set and get
        await db.set_privacy_preferred_name(user_id, PrivacyType.PUBLIC)
        await db.set_privacy_pronouns(user_id, PrivacyType.PUBLIC)
        await db.set_privacy_birthday(user_id, PrivacyType.PUBLIC)
        await db.set_privacy_age(user_id, PrivacyType.PUBLIC)
        await db.set_privacy_timezone(user_id, PrivacyType.PUBLIC)
        await assert_all_privacies(PrivacyType.PUBLIC)

        # Delete user
        await db.delete_user(user_id)
        await assert_all_privacies(PrivacyType.PRIVATE)

    async def test_info(self):
        db = self._db

        user_id = 123
        name = 'Greg'
        pronouns = 'He/Him'
        birthday = dt.date(2000, 6, 1)
        birthday_20years = dt.date(2020, 6, 1)
        timezone = pytz.timezone('America/New_York')

        async def assert_all_none():
            self.assertIsNone(await db.get_preferred_name(user_id))
            self.assertIsNone(await db.get_pronouns(user_id))
            self.assertIsNone(await db.get_birthday(user_id))
            self.assertIsNone(await db.get_age(user_id))
            self.assertIsNone(await db.get_timezone(user_id))

        async def set_and_assert_equals():
            await db.set_preferred_name(user_id, name)
            await db.set_pronouns(user_id, pronouns)
            await db.set_birthday(user_id, birthday)
            await db.set_timezone(user_id, timezone)
            self.assertEqual(await db.get_preferred_name(user_id), name)
            self.assertEqual(await db.get_pronouns(user_id), pronouns)
            self.assertEqual(await db.get_birthday(user_id), birthday)
            self.assertEqual(await db.get_timezone(user_id), timezone)

        # Nonexistent user
        await assert_all_none()

        # Basic
        await set_and_assert_equals()

        # Can't reliably test db.get_age since today is always changing, so
        # first assert that get_age is an int, then test the age calculation
        # method with static dates
        self.assertIsInstance(await db.get_age(user_id), int)
        self.assertEqual(
            db._calculate_age(birthday, birthday_20years - dt.timedelta(days=1)),
            19
        )
        self.assertEqual(
            db._calculate_age(birthday, birthday_20years),
            20
        )
        self.assertEqual(
            db._calculate_age(birthday, birthday_20years + dt.timedelta(days=1)),
            20
        )

        # Clear fields
        await db.set_preferred_name(user_id, None)
        await db.set_pronouns(user_id, None)
        await db.set_birthday(user_id, None)
        await db.set_timezone(user_id, None)
        await assert_all_none()

        # Set fields again and test delete user
        await set_and_assert_equals()
        await db.delete_user(user_id)
        await assert_all_none()

    async def test_find_users_by_preferred_name(self):
        db = self._db

        # No users in table
        found = await db.find_users_by_preferred_name('anything')
        self.assertEqual(found, [])

        await db.set_preferred_name(1, 'Greg')
        await db.set_preferred_name(2, 'Pizzaman')
        await db.set_preferred_name(3, 'Eat pizza')
        await db.set_preferred_name(4, 'Fred')
        await db.set_preferred_name(5, 'Fred')
        await db.set_preferred_name(6, 'fred')
        await db.set_preferred_name(7, 'Ned')
        await db.set_preferred_name(8, 'Ned')
        for i in range(1, 8):
            await db.set_privacy_preferred_name(i, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(8, PrivacyType.PRIVATE)

        # Empty and missing names
        found = await db.find_users_by_preferred_name('')
        self.assertEqual(found, [])
        found = await db.find_users_by_preferred_name('Not a name')
        self.assertEqual(found, [])

        # Input case insensitivity
        found = await db.find_users_by_preferred_name('Greg')
        self.assertCountEqual(found, [(1, 'Greg')])
        found = await db.find_users_by_preferred_name('greg')
        self.assertCountEqual(found, [(1, 'Greg')])

        # Substrings
        found = await db.find_users_by_preferred_name('pizza')
        self.assertCountEqual(found, [(2, 'Pizzaman'), (3, 'Eat pizza')])
        found = await db.find_users_by_preferred_name('pizzaman')
        self.assertCountEqual(found, [(2, 'Pizzaman')])

        # Duplicates and output case insensitivity
        found = await db.find_users_by_preferred_name('Fred')
        self.assertCountEqual(found, [(4, 'Fred'), (5, 'Fred'), (6, 'fred')])

        # Private name
        found = await db.find_users_by_preferred_name('Ned')
        self.assertCountEqual(found, [(7, 'Ned')])

    async def test_get_all_timezones(self):
        db = self._db

        tz_london = pytz.timezone('Europe/London')
        tz_new_york = pytz.timezone('America/New_York')
        tz_denver = pytz.timezone('America/Denver')
        tz_boise = pytz.timezone('America/Boise')

        # No users in table
        timezones = await db.get_all_timezones()
        self.assertEqual(timezones, [])

        # Basic
        await db.set_timezone(1, tz_london)
        await db.set_privacy_timezone(1, PrivacyType.PUBLIC)
        timezones = await db.get_all_timezones()
        self.assertCountEqual(timezones, [(1, tz_london)])

        # Duplicate timezones
        await db.set_timezone(2, tz_london)
        await db.set_privacy_timezone(2, PrivacyType.PUBLIC)
        timezones = await db.get_all_timezones()
        self.assertCountEqual(timezones, [(1, tz_london), (2, tz_london)])

        # More timezones and private timezone
        await db.set_timezone(3, tz_new_york)
        await db.set_timezone(4, tz_denver)
        await db.set_timezone(5, tz_boise)
        await db.set_privacy_timezone(3, PrivacyType.PUBLIC)
        await db.set_privacy_timezone(4, PrivacyType.PUBLIC)
        await db.set_privacy_timezone(5, PrivacyType.PRIVATE)
        timezones = await db.get_all_timezones()
        self.assertCountEqual(
            timezones,
            [(1, tz_london), (2, tz_london), (3, tz_new_york), (4, tz_denver)]
        )
