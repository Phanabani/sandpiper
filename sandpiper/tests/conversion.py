import datetime as dt
import unittest
import unittest.mock as mock
from typing import Optional, Union

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from sandpiper.conversion.cog import Conversion
from sandpiper.conversion.unit_conversion import imperial_shorthand_pattern
from sandpiper.user_data import DatabaseSQLite, UserData
from sandpiper.user_data.enums import PrivacyType

__all__ = ['TestImperialShorthandRegex', 'TestConversion']

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


class TestConversion(DiscordMockingTestCase):

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

    def setup_cogs(self, bot: commands.Bot):
        bot.add_cog(Conversion(bot))
        bot.add_cog(UserData(bot))

    async def test_unit_conversion(self):
        self.msg.author.id = 0
        msgs = await self.dispatch_msg_get_msgs(
            "guys it's {30f} outside today, I'm so cold...")
        self.assertIn('30.00 °F', msgs[0])
        self.assertIn('-1.11 °C', msgs[0])

        msgs = await self.dispatch_msg_get_msgs(
            "I've been working out a lot lately and I've already lost {2 kg}!!")
        self.assertIn('4.41 lb', msgs[0])
        self.assertIn('2.00 kg', msgs[0])

        msgs = await self.dispatch_msg_get_msgs(
            "I think Jason is like {6' 2\"} tall")
        self.assertIn('6.17 ft', msgs[0])
        self.assertIn('1.88 m', msgs[0])

        msgs = await self.dispatch_msg_get_msgs(
            "I'm only {5'11\"} though!")
        self.assertIn('5.92 ft', msgs[0])
        self.assertIn('1.80 m', msgs[0])

        msgs = await self.dispatch_msg_get_msgs(
            "Is that a {33ft} boat, TJ?")
        self.assertIn('33.00 ft', msgs[0])
        self.assertIn('10.06 m', msgs[0])

        msgs = await self.dispatch_msg_get_msgs(
            "Lou lives about {15km} from me and TJ's staying at a hotel "
            "{2.5km} away, so he and I are gonna meet up and drive over to "
            "Lou."
        )
        self.assertIn('9.32 mi', msgs[0])
        self.assertIn('15.00 km', msgs[0])
        self.assertIn('1.55 mi', msgs[0])
        self.assertIn('2.50 km', msgs[0])

    # @mock.patch('sandpiper.tests.conversion.dt.datetime')
    @mock.patch('sandpiper.common.time.tzlocal.get_localzone', autospec=True)
    @mock.patch('sandpiper.common.time.dt', autospec=True)
    async def test_time_conversion(self, mock_datetime, mock_localzone):
        mock_localzone.return_value = pytz.UTC
        mock_datetime.datetime.now.return_value = dt.datetime(2020, 6, 1, 9, 32)
        mock_datetime.datetime.side_effect = (
            lambda *args, **kw: dt.datetime(*args, **kw))
        mock_datetime.date.side_effect = (
            lambda *args, **kw: dt.date(*args, **kw))
        mock_datetime.time.side_effect = (
            lambda *args, **kw: dt.time(*args, **kw))

        self.msg.guild.get_member.return_value = True

        dutch_user = 123
        dutch_tz = pytz.timezone('Europe/Amsterdam')
        dutch_now = dt.datetime.now().astimezone(dutch_tz)
        british_user = 456
        british_tz = pytz.timezone('Europe/London')
        british_now = dt.datetime.now().astimezone(british_tz)
        american_user = 789
        american_tz = pytz.timezone('America/New_York')
        american_now = dt.datetime.now().astimezone(american_tz)
        await self.db.set_timezone(dutch_user, dutch_tz)
        await self.db.set_timezone(british_user, british_tz)
        await self.db.set_timezone(american_user, american_tz)
        await self.db.set_privacy_timezone(dutch_user, PrivacyType.PUBLIC)
        await self.db.set_privacy_timezone(british_user, PrivacyType.PUBLIC)
        await self.db.set_privacy_timezone(american_user, PrivacyType.PUBLIC)

        self.msg.author.id = dutch_user
        msgs = await self.dispatch_msg_get_msgs(
            "do you guys wanna play at {9pm}?")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+9:00 PM')
        self.assertRegex(msgs[0], r'Europe/London.+8:00 PM')
        self.assertRegex(msgs[0], r'America/New_York.+3:00 PM')

        self.msg.author.id = american_user
        msgs = await self.dispatch_msg_get_msgs(
            "I wish I could, but I'm busy from {14} to {17:45}")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+8:00 PM.+11:45 PM')
        self.assertRegex(msgs[0], r'Europe/London.+7:00 PM.+10:45 PM')
        self.assertRegex(msgs[0], r'America/New_York.+2:00 PM.+5:45 PM')

        self.msg.author.id = american_user
        msgs = await self.dispatch_msg_get_msgs(
            "I get off work at {330pm}")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+9:30 PM')
        self.assertRegex(msgs[0], r'Europe/London.+8:30 PM')
        self.assertRegex(msgs[0], r'America/New_York.+3:30 PM')

        self.msg.author.id = american_user
        msgs = await self.dispatch_msg_get_msgs(
            "In 24-hour time that's {1530}")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+9:30 PM')
        self.assertRegex(msgs[0], r'Europe/London.+8:30 PM')
        self.assertRegex(msgs[0], r'America/New_York.+3:30 PM')

        self.msg.author.id = american_user
        msgs = await self.dispatch_msg_get_msgs(
            "Dude, it's {midnight} :gobed:!")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+6:00 AM')
        self.assertRegex(msgs[0], r'Europe/London.+5:00 AM')
        self.assertRegex(msgs[0], r'America/New_York.+12:00 AM')

        self.msg.author.id = british_user
        msgs = await self.dispatch_msg_get_msgs(
            "yeah I've gotta wake up at {5} for work tomorrow, so it's an "
            "early bedtime for me"
        )
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+6:00 AM')
        self.assertRegex(msgs[0], r'Europe/London.+5:00 AM')
        self.assertRegex(msgs[0], r'America/New_York.+12:00 AM')

        self.msg.author.id = dutch_user
        msgs = await self.dispatch_msg_get_msgs(
            "It's nearly {noon}. Time for lunch!")
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+12:00 PM')
        self.assertRegex(msgs[0], r'Europe/London.+11:00 AM')
        self.assertRegex(msgs[0], r'America/New_York.+6:00 AM')

        self.msg.author.id = british_user
        msgs = await self.dispatch_msg_get_msgs(
            "I'm free {now}, anyone want to do something?"
        )
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+' + dutch_now.strftime("%I:%M %p").lstrip("0"))
        self.assertRegex(msgs[0], r'Europe/London.+' + british_now.strftime("%I:%M %p").lstrip("0"))
        self.assertRegex(msgs[0], r'America/New_York.+' + american_now.strftime("%I:%M %p").lstrip("0"))
