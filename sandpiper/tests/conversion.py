import datetime as dt
import unittest.mock as mock

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from ..user_data import DatabaseSQLite, UserData
from sandpiper.conversion.cog import Conversion

__all__ = ['TestConversion']

from ..user_data.enums import PrivacyType

CONNECTION = ':memory:'


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
        dutch_user = 123
        await self.db.set_timezone(dutch_user, pytz.timezone('Europe/Amsterdam'))
        await self.db.set_privacy_timezone(dutch_user, PrivacyType.PUBLIC)

        self.msg.author.id = dutch_user
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
        mock_datetime.datetime.now.return_value = dt.datetime(2020, 6, 1)
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

        self.msg.author.id = british_user
        msgs = await self.dispatch_msg_get_msgs(
            "yeah I've gotta wake up at {5} for work tomorrow, so it's an "
            "early bedtime for me"
        )
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+6:00 AM')
        self.assertRegex(msgs[0], r'Europe/London.+5:00 AM')
        self.assertRegex(msgs[0], r'America/New_York.+12:00 AM')

        self.msg.author.id = british_user
        msgs = await self.dispatch_msg_get_msgs(
            "I'm free {now}, anyone want to do something?"
        )
        self.assertRegex(msgs[0], r'Europe/Amsterdam.+' + dutch_now.strftime("%I:%M %p").lstrip("0"))
        self.assertRegex(msgs[0], r'Europe/London.+' + british_now.strftime("%I:%M %p").lstrip("0"))
        self.assertRegex(msgs[0], r'America/New_York.+' + american_now.strftime("%I:%M %p").lstrip("0"))
