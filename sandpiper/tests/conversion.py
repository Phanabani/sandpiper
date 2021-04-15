import datetime as dt
import unittest
import unittest.mock as mock
from typing import *

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from sandpiper.common.time import utc_now
from sandpiper.conversion.cog import Conversion
from sandpiper.conversion.unit_conversion import imperial_shorthand_pattern
from sandpiper.user_data import DatabaseSQLite, UserData
from sandpiper.user_data.enums import PrivacyType

__all__ = (
    'TestImperialShorthandRegex',
    'TestUnitConversion',
    'TestTimeConversion'
)

CONNECTION = ':memory:'


class TestImperialShorthandRegex(unittest.TestCase):

    def assert_match(
            self, test_str: str, foot: Optional[Union[int, float]],
            inch: Optional[Union[int, float]]
    ):
        match = imperial_shorthand_pattern.match(test_str)

        if foot is None and inch is None:
            self.assertIsNone(match)
        else:
            match_foot = match['foot']
            match_inch = match['inch']
            # Coerce the matched strings into their expected types
            if foot is not None and match_foot is not None:
                match_foot = type(foot)(match_foot)
            if inch is not None and match_inch is not None:
                match_inch = type(inch)(match_inch)

            self.assertEqual(match_foot, foot)
            self.assertEqual(match_inch, inch)

    def test_int_feet(self):
        self.assert_match("1'", 1, None)
        self.assert_match("23'", 23, None)
        self.assert_match("-4'", None, None)
        self.assert_match(" 5'", None, None)

    def test_int_inches(self):
        self.assert_match("1\"", None, 1)
        self.assert_match("23\"", None, 23)
        self.assert_match("-4\"", None, None)
        self.assert_match(" 5\"", None, None)

    def test_int_both(self):
        self.assert_match("1'2\"", 1, 2)
        self.assert_match("3' 4\"", 3, 4)
        self.assert_match("56' 78\"", 56, 78)
        self.assert_match("0' 1\"", 0, 1)
        self.assert_match("1' 0\"", 1, 0)

    def test_decimal_feet(self):
        # Decimal feet are not allowed (yet?)
        self.assert_match("1.2'", None, None)
        self.assert_match("0.3'", None, None)
        self.assert_match(".4'", None, None)

    def test_decimal_inches(self):
        self.assert_match("1.2\"", None, 1.2)
        self.assert_match("0.3\"", None, 0.3)
        self.assert_match(".4\"", None, 0.4)

    def test_decimal_both(self):
        self.assert_match("1' 2.3\"", 1, 2.3)
        self.assert_match(".4' 5.6\"", None, None)
        self.assert_match("1' 2.3.4\"", None, None)

    def test_other_garbage(self):
        self.assert_match("", None, None)
        self.assert_match("5", None, None)
        self.assert_match("30.00 °F", None, None)


class TestUnitConversion(DiscordMockingTestCase):

    def add_cogs(self, bot: commands.Bot):
        bot.add_cog(Conversion(bot))

    async def test_unit_conversion(self):
        await self.assert_in_reply(
            "guys it's {30f} outside today, I'm so cold...",
            '30.00 °F', '-1.11 °C'
        )
        await self.assert_in_reply(
            "I've been working out a lot lately and I've already lost {2 kg}!!",
            '4.41 lb', '2.00 kg'
        )
        await self.assert_in_reply(
            "I think Jason is like {6' 2\"} tall",
            '6.17 ft', '1.88 m'
        )
        await self.assert_in_reply(
            "I'm only {5'11\"} though!",
            '5.92 ft', '1.80 m'
        )
        await self.assert_in_reply(
            "Is that a {33ft} boat, TJ?",
            '33.00 ft', '10.06 m'
        )
        await self.assert_in_reply(
            "Lou lives about {15km} from me and TJ's staying at a hotel "
            "{2.5km} away, so he and I are gonna meet up and drive over to "
            "Lou.",
            '9.32 mi', '15.00 km',
            '1.55 mi', '2.50 km'
        )
        await self.assert_in_reply(
            "I was only {4 yards} away in geoguessr!!",
            '4.00 yd', '3.66 m'
        )


def patch_time(f: Callable):
    @mock.patch('sandpiper.common.time.tzlocal.get_localzone', autospec=True)
    @mock.patch('sandpiper.common.time.dt', autospec=True)
    async def decorated(self, mock_datetime, mock_localzone):
        mock_localzone.return_value = pytz.UTC
        mock_datetime.datetime.now.return_value = dt.datetime(2020, 6, 1, 9, 32)
        mock_datetime.datetime.side_effect = (
            lambda *a, **kw: dt.datetime(*a, **kw)
        )
        mock_datetime.date.side_effect = (
            lambda *a, **kw: dt.date(*a, **kw)
        )
        mock_datetime.time.side_effect = (
            lambda *a, **kw: dt.time(*a, **kw)
        )
        await f(self, mock_datetime, mock_localzone)

    return decorated


class TestTimeConversion(DiscordMockingTestCase):

    db: DatabaseSQLite

    async def asyncSetUp(self):
        await super().asyncSetUp()

        # Connect to a dummy database
        self.db = DatabaseSQLite(CONNECTION)
        await self.db.connect()

        # Bypass UserData cog lookup by patching in the database
        patcher = mock.patch(
            'sandpiper.user_data.UserData.get_database',
            return_value=self.db
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        await self.db.disconnect()

    def add_cogs(self, bot: commands.Bot):
        bot.add_cog(Conversion(bot))
        bot.add_cog(UserData(bot))

    async def add_timezone_user(self, timezone: str) -> Tuple[int, dt.datetime]:
        uid = self.new_user_id()
        tz = pytz.timezone(timezone)
        now = utc_now().astimezone(tz)
        await self.db.set_timezone(uid, tz)
        await self.db.set_privacy_timezone(uid, PrivacyType.PUBLIC)
        return uid, now

    # noinspection PyUnusedLocal
    @patch_time
    async def test_time_conversion(self, mock_datetime, mock_localzone):
        dutch_user, dutch_now = await self.add_timezone_user('Europe/Amsterdam')
        british_user, british_now = await self.add_timezone_user('Europe/London')
        american_user, american_now = await self.add_timezone_user('America/New_York')

        self.msg.author.id = dutch_user
        await self.assert_regex_reply(
            "do you guys wanna play at {9pm}?",
            r'Europe/Amsterdam.+9:00 PM',
            r'Europe/London.+8:00 PM',
            r'America/New_York.+3:00 PM'
        )

        self.msg.author.id = american_user
        await self.assert_regex_reply(
            "I wish I could, but I'm busy from {14} to {17:45}",
            r'Europe/Amsterdam.+8:00 PM.+11:45 PM',
            r'Europe/London.+7:00 PM.+10:45 PM',
            r'America/New_York.+2:00 PM.+5:45 PM'
        )

        self.msg.author.id = american_user
        await self.assert_regex_reply(
            "I get off work at {330pm}",
            r'Europe/Amsterdam.+9:30 PM',
            r'Europe/London.+8:30 PM',
            r'America/New_York.+3:30 PM'
        )

        self.msg.author.id = american_user
        await self.assert_regex_reply(
            "In 24-hour time that's {1530}",
            r'Europe/Amsterdam.+9:30 PM',
            r'Europe/London.+8:30 PM',
            r'America/New_York.+3:30 PM'
        )

        self.msg.author.id = american_user
        await self.assert_regex_reply(
            "Dude, it's {midnight} :gobed:!",
            r'Europe/Amsterdam.+6:00 AM',
            r'Europe/London.+5:00 AM',
            r'America/New_York.+12:00 AM'
        )

        self.msg.author.id = british_user
        await self.assert_regex_reply(
            "yeah I've gotta wake up at {5} for work tomorrow, so it's an "
            "early bedtime for me",
            r'Europe/Amsterdam.+6:00 AM',
            r'Europe/London.+5:00 AM',
            r'America/New_York.+12:00 AM'
        )

        self.msg.author.id = dutch_user
        await self.assert_regex_reply(
            "It's nearly {noon}. Time for lunch!",
            r'Europe/Amsterdam.+12:00 PM',
            r'Europe/London.+11:00 AM',
            r'America/New_York.+6:00 AM'
        )

        self.msg.author.id = british_user
        await self.assert_regex_reply(
            "I'm free {now}, anyone want to do something?",
            r'Europe/Amsterdam.+' + dutch_now.strftime("%I:%M %p").lstrip("0"),
            r'Europe/London.+' + british_now.strftime("%I:%M %p").lstrip("0"),
            r'America/New_York.+' + american_now.strftime("%I:%M %p").lstrip("0")
        )
