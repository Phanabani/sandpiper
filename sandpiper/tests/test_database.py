import datetime as dt

import pytest
import pytz

from ._helpers import *
from sandpiper.common.time import TimezoneType
from sandpiper.user_data import DatabaseSQLite
from sandpiper.user_data.enums import PrivacyType

pytestmark = pytest.mark.asyncio


@pytest.fixture
def user_id(new_id) -> int:
    return new_id()


class TestConnection:

    async def test_connected(self, database):
        assert (await database.connected()) is True

    async def test_disconnected(self):
        database = DatabaseSQLite(':memory:')
        await database.connect()
        await database.disconnect()
        assert (await database.connected()) is False


class TestPreferredName:

    async def test_get(self, database, user_id):
        assert (await database.get_preferred_name(user_id)) is None

    async def test_set_get(self, database, user_id):
        value = 'Greg'
        await database.set_preferred_name(user_id, value)
        assert (await database.get_preferred_name(user_id)) == value

    async def test_privacy_get(self, database, user_id):
        assert (await database.get_privacy_preferred_name(user_id)) is None

    async def test_privacy_set_get(self, database, user_id):
        value = PrivacyType.PUBLIC
        await database.set_privacy_preferred_name(user_id, value)
        assert (await database.get_privacy_preferred_name(user_id)) is value


class TestPronouns:

    async def test_get(self, database, user_id):
        assert (await database.get_pronouns(user_id)) is None

    async def test_set_get(self, database, user_id):
        value = 'She/Her'
        await database.set_pronouns(user_id, value)
        assert (await database.get_pronouns(user_id)) == value

    async def test_privacy_get(self, database, user_id):
        assert (await database.get_privacy_pronouns(user_id)) is None

    async def test_privacy_set_get(self, database, user_id):
        value = PrivacyType.PUBLIC
        await database.set_privacy_pronouns(user_id, value)
        assert (await database.get_privacy_pronouns(user_id)) is value


class TestBirthday:

    async def test_get(self, database, user_id):
        assert (await database.get_birthday(user_id)) is None

    async def test_set_get(self, database, user_id):
        value = dt.date(2000, 2, 14)
        await database.set_birthday(user_id, value)
        assert (await database.get_birthday(user_id)) == value

    async def test_privacy_get(self, database, user_id):
        assert (await database.get_privacy_birthday(user_id)) is None

    async def test_privacy_set_get(self, database, user_id):
        value = PrivacyType.PUBLIC
        await database.set_privacy_birthday(user_id, value)
        assert (await database.get_privacy_birthday(user_id)) is value


class TestAge:

    async def test_privacy_get(self, database, user_id):
        assert (await database.get_privacy_age(user_id)) is None

    async def test_privacy_set_get(self, database, user_id):
        value = PrivacyType.PUBLIC
        await database.set_privacy_age(user_id, value)
        assert (await database.get_privacy_age(user_id)) is value


class TestTimezone:

    async def test_get(self, database, user_id):
        assert (await database.get_timezone(user_id)) is None

    async def test_set_get(self, database, user_id):
        value = pytz.timezone('America/New_York')
        await database.set_timezone(user_id, value)
        assert (await database.get_timezone(user_id)) == value

    async def test_privacy_get(self, database, user_id):
        assert (await database.get_privacy_timezone(user_id)) is None

    async def test_privacy_set_get(self, database, user_id):
        value = PrivacyType.PUBLIC
        await database.set_privacy_timezone(user_id, value)
        assert (await database.get_privacy_timezone(user_id)) is value


class TestFindUsersByPreferredName:

    @pytest.fixture()
    def user_factory(self, database, new_id):
        async def f(
                preferred_name: str, privacy: PrivacyType = PrivacyType.PUBLIC
        ) -> int:
            uid = new_id()
            await database.set_preferred_name(uid, preferred_name)
            await database.set_privacy_preferred_name(uid, privacy)
            return uid
        return f

    async def test_no_users(self, database):
        found = await database.find_users_by_preferred_name('Name')
        assert found == []

    async def test_no_users_with_name(self, database, user_factory):
        await user_factory('Greg')
        found = await database.find_users_by_preferred_name('Alan')
        assert found == []

    async def test_basic(self, database, user_factory):
        uid = await user_factory('Greg')
        found = await database.find_users_by_preferred_name('Greg')
        assert found == [(uid, 'Greg')]

    async def test_empty_string(self, database, user_factory):
        await user_factory('Greg')
        found = await database.find_users_by_preferred_name('')
        assert found == []

    async def test_duplicate(self, database, user_factory):
        uid1 = await user_factory('Fred')
        uid2 = await user_factory('Fred')
        found = await database.find_users_by_preferred_name('Fred')
        assert_count_equal(found, [(uid1, 'Fred'), (uid2, 'Fred')])

    async def test_case_insensitive(self, database, user_factory):
        uid1 = await user_factory('Ned')
        uid2 = await user_factory('ned')
        found = await database.find_users_by_preferred_name('ned')
        assert_count_equal(found, [(uid1, 'Ned'), (uid2, 'ned')])

    async def test_substring(self, database, user_factory):
        uid1 = await user_factory('Pizzaman')
        uid2 = await user_factory('Eat Pizza')
        found = await database.find_users_by_preferred_name('Pizza')
        assert_count_equal(found, [(uid1, 'Pizzaman'), (uid2, 'Eat Pizza')])

    async def test_superstring(self, database, user_factory):
        uid1 = await user_factory('Pizzaman')
        uid2 = await user_factory('Eat Pizza')
        found = await database.find_users_by_preferred_name('Pizzaman')
        assert found == [(uid1, 'Pizzaman')]

    async def test_private(self, database, user_factory):
        uid1 = await user_factory('Alan')
        uid2 = await user_factory('Alan', PrivacyType.PRIVATE)
        found = await database.find_users_by_preferred_name('Alan')
        assert found == [(uid1, 'Alan')]


class TestGetBirthdaysRange:

    @pytest.fixture()
    def user_factory(self, database, new_id):
        async def f(
                birthday: dt.date, privacy: PrivacyType = PrivacyType.PUBLIC
        ) -> int:
            uid = new_id()
            await database.set_birthday(uid, birthday)
            await database.set_privacy_birthday(uid, privacy)
            return uid
        return f

    @pytest.fixture()
    async def birthdays(self, user_factory) -> list[tuple[int, dt.date]]:
        dates = (
            dt.date(3, 10, 2000),
            dt.date(3, 15, 1992),
            dt.date(4, 5, 2004),
            dt.date(4, 30, 2000),
            dt.date(5, 2, 1999),
            dt.date(5, 27, 1998)
        )
        yield [(await user_factory(bday), bday) for bday in dates]

    async def test_no_results(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(2, 1, 2021), dt.date(2, 20, 2021)
        )
        assert result == []

    async def test_same_month(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(4, 4, 2021), dt.date(4, 25, 2021)
        )
        assert_count_equal(result, [birthdays[2]])

    async def test_multiple_months(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(4, 21, 2021), dt.date(5, 15, 2021)
        )
        assert_count_equal(result, [birthdays[3], birthdays[4]])

    async def test_inclusive(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(4, 5, 2021), dt.date(4, 30, 2021)
        )
        assert_count_equal(result, [birthdays[2], birthdays[3]])

    async def test_year_agnostic(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(4, 21, 582), dt.date(5, 15, 4827)
        )
        assert_count_equal(result, [birthdays[3], birthdays[4]])

    async def test_year_wraparound(self, database, birthdays):
        result = await database.get_birthdays_range(
            dt.date(5, 1, 2020), dt.date(3, 13, 2020)
        )
        assert_count_equal(result, [birthdays[4], birthdays[5], birthdays[0]])


class TestGetAllTimezones:

    @pytest.fixture()
    def user_factory(self, database, new_id):
        async def f(
                timezone: TimezoneType,
                privacy: PrivacyType = PrivacyType.PUBLIC
        ) -> int:
            uid = new_id()
            await database.set_timezone(uid, timezone)
            await database.set_privacy_timezone(uid, privacy)
            return uid
        return f

    @pytest.fixture()
    def tz_london(self):
        return pytz.timezone('Europe/London')

    @pytest.fixture()
    def tz_new_york(self):
        return pytz.timezone('America/New_York')

    @pytest.fixture()
    def tz_denver(self):
        return pytz.timezone('America/Denver')

    @pytest.fixture()
    def tz_boise(self):
        return pytz.timezone('America/Boise')

    async def test_no_users(self, database, user_factory):
        timezones = await database.get_all_timezones()
        assert timezones == []

    async def test_basic(self, database, user_factory, tz_london):
        uid = await user_factory(tz_london)
        timezones = await database.get_all_timezones()
        assert timezones == [(uid, tz_london)]

    async def test_many(
            self, database, user_factory, tz_london, tz_new_york, tz_denver,
            tz_boise
    ):
        uid1 = await user_factory(tz_london)
        uid2 = await user_factory(tz_new_york)
        uid3 = await user_factory(tz_denver)
        uid4 = await user_factory(tz_boise)
        timezones = await database.get_all_timezones()
        assert_count_equal(
            timezones, [
                (uid1, tz_london), (uid2, tz_new_york), (uid3, tz_denver),
                (uid4, tz_boise)
            ]
        )

    async def test_duplicate(self, database, user_factory, tz_london):
        uid1 = await user_factory(tz_london)
        uid2 = await user_factory(tz_london)
        timezones = await database.get_all_timezones()
        assert_count_equal(timezones, [(uid1, tz_london), (uid2, tz_london)])

    async def test_private(
            self, database, user_factory, tz_new_york, tz_denver
    ):
        uid1 = await user_factory(tz_new_york)
        uid2 = await user_factory(tz_denver, PrivacyType.PRIVATE)
        timezones = await database.get_all_timezones()
        assert timezones == [(uid1, tz_new_york)]
