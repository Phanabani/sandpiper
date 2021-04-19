import datetime as dt
from typing import *
import unittest
import unittest.mock as mock

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from sandpiper.common.time import utc_now
from sandpiper.conversion.cog import Conversion, conversion_pattern
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
        __tracebackhide__ = True
        match = imperial_shorthand_pattern.match(test_str)

        if foot is None and inch is None:
            assert match is None
        else:
            match_foot = match['foot']
            match_inch = match['inch']
            # Coerce the matched strings into their expected types
            if foot is not None and match_foot is not None:
                match_foot = type(foot)(match_foot)
            if inch is not None and match_inch is not None:
                match_inch = type(inch)(match_inch)

            assert match_foot == foot
            assert match_inch == inch

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


class TestConversionStringRegex(unittest.TestCase):

    def assert_match(
            self, in_: str, quantity: Optional[str], out_unit: Optional[str]
    ):
        __tracebackhide__ = True
        match = conversion_pattern.match(in_)

        if quantity is None:
            if out_unit is not None:
                raise ValueError("Cannot test for only out_unit")
            assert match is None, "Pattern matched when it shouldn't have"
            return

        assert match['quantity'] == quantity, (
            f"Matched quantity {match['quantity']} does not equal input "
            f"{quantity}"
        )
        assert match['out_unit'] == out_unit, (
            f"Matched out unit {match['out_unit']} does not equal input "
            f"{out_unit}"
        )

    def test_simple(self):
        self.assert_match('{5pm}', '5pm', None)
        self.assert_match('{ 5 ft }', '5 ft', None)

    def test_specifier_with_out_unit(self):
        self.assert_match('{5ft>m}', '5ft', 'm')
        self.assert_match('{5ft > m}', '5ft', 'm')
        self.assert_match('{5 ft > m}', '5 ft', 'm')
        self.assert_match('{5 km  >  mi}', '5 km', 'mi')
        self.assert_match('{ 5pm  > new york}', '5pm', 'new york')
        self.assert_match('{ 5pm  > new york   }', '5pm', 'new york')

    def test_specifier_no_out_unit(self):
        self.assert_match('{5pm>}', None, None)
        self.assert_match('{5pm >}', None, None)
        self.assert_match('{5pm> }', None, None)
        self.assert_match('{5pm > }', None, None)
        self.assert_match('{8:00 > }', None, None)


class TestUnitConversion(DiscordMockingTestCase):

    def add_cogs(self, bot: commands.Bot):
        bot.add_cog(Conversion(bot))

    async def assert_error(self, msg: str, *substrings: str):
        __tracebackhide__ = True
        embed = await self.dispatch_msg_get_embeds(msg, only_one=True)
        super().assert_error(embed, *substrings)

    async def test_two_way(self):
        await self.assert_in_reply(
            "guys it's {30f} outside today, I'm so cold...",
            '30.00 °F', '-1.11 °C'
        )
        await self.assert_in_reply(
            "guys it's {-1.11c} outside today, I'm so cold...",
            '30.00 °F', '-1.11 °C'
        )
        await self.assert_in_reply(
            "I've been working out a lot lately and I've already lost {2 kg}!!",
            '2.00 kg', '4.41 lb'
        )
        await self.assert_in_reply(
            "I've been working out a lot lately and I've already lost {4.41 lb}!!",
            '2.00 kg', '4.41 lb'
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

    async def test_one_way(self):
        await self.assert_in_reply(
            "I was only {4 yards} away in geoguessr!!",
            '4.00 yd', '3.66 m'
        )
        await self.assert_in_reply(
            "I weigh around {9.3 stone}. whatever that means...",
            '9.30 stone', '59.06 kg'
        )
        await self.assert_in_reply(
            "any scientists in the chat?? {0 K}",
            '0.00 K', '-273.15 °C'
        )

    async def test_imperial_shorthand(self):
        await self.assert_in_reply(
            "I think Jason is like {6' 2\"} tall",
            '6.17 ft', '1.88 m'
        )
        await self.assert_in_reply(
            "I'm only {5'11\"} though!",
            '5.92 ft', '1.80 m'
        )

    async def test_explicit(self):
        await self.assert_in_reply(
            "{-5 f > kelvin} it's too late for apologies, imperial system",
            '-5.00 °F', '252.59 K'
        )
        await self.assert_in_reply(
            "how much is {9.3 stone > lbs}",
            '9.30 stone', '130.20 lb'
        )
        await self.assert_in_reply(
            "bc this is totally useful.. {5 mi > ft}"
            '5 mi', '26400.00 ft'
        )
        await self.assert_in_reply(
            "can't believe {3.000 hogshead > gallon} is even real"
            '3 hogshead', '189.00 gal'
        )
        await self.assert_in_reply(
            "ma'am you forgot your spaces {5ft>yd}",
            '5.00 ft', '1.67 yd'
        )

    async def test_unit_math(self):
        await self.assert_in_reply(
            "I'm measuring wood planks, I need {2.3 ft + 5 in}",
            '2.72 ft', '0.83 m'
        )
        await self.assert_in_reply(
            "oops, I need that in inches {2.3 ft + 5 in > in}",
            '2.72 ft', '32.60 in'
        )
        await self.assert_in_reply(
            "my two favorite songs are a total of {5min+27s + 4min+34s > s}",
            '10.02 min', '601.00 s'
        )

    async def test_dimensionless_math(self):
        await self.assert_in_reply(
            "what's {2 + 7}?",
            '2 + 7', '9'
        )
        await self.assert_in_reply(
            "how about {2.5 + 7.8}?",
            '2.5 + 7.8', '10.3'
        )
        await self.assert_in_reply(
            "and {2 * 7}?",
            '2 * 7', '14'
        )

    async def test_unknown_unit(self):
        await self.assert_error(
            "that's like {12.5 donuts} wide!",
            'Unknown unit "donuts"'
        )
        await self.assert_error(
            "how far away is that in blehs? {6 km > bleh}",
            'Unknown unit "bleh"'
        )

    async def test_unmapped_unit(self):
        await self.assert_error(
            "{5 hogshead} is a real unit, but not really useful enough to be "
            "mapped. fun name though",
            '{5 hogshead > otherunit}'
        )

    async def test_bad_conversion_string(self):
        await self.assert_no_reply("oops I dropped my unit {5 ft >}",)
        await self.assert_no_reply("oh crap not again {5 ft > }",)
        await self.assert_no_reply("okay this is just disgusting {5 >}",)
        await self.assert_no_reply("dude! {5 > }",)


class TestTimeConversion(DiscordMockingTestCase):

    db: DatabaseSQLite
    MOCK_NOW = dt.datetime(2020, 6, 1, 9, 32)

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

        self.patch_time()

        self.dutch_user, self.dutch_now = await self.add_timezone_user('Europe/Amsterdam')
        self.british_user, self.british_now = await self.add_timezone_user('Europe/London')
        self.american_user, self.american_now = await self.add_timezone_user('America/New_York')

    def patch_time(self):
        # Patch datetime to use a static datetime
        patcher = mock.patch('sandpiper.common.time.dt', autospec=True)
        mock_datetime = patcher.start()
        self.addCleanup(patcher.stop)

        mock_datetime.datetime.now.return_value = self.MOCK_NOW
        mock_datetime.datetime.side_effect = (
            lambda *a, **kw: dt.datetime(*a, **kw)
        )
        mock_datetime.date.side_effect = (
            lambda *a, **kw: dt.date(*a, **kw)
        )
        mock_datetime.time.side_effect = (
            lambda *a, **kw: dt.time(*a, **kw)
        )

        # Patch localzone to use UTC
        patcher = mock.patch(
            'sandpiper.common.time.tzlocal.get_localzone', autospec=True
        )
        mock_localzone = patcher.start()
        self.addCleanup(patcher.stop)

        mock_localzone.return_value = pytz.UTC

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

    async def assert_error(self, msg: str, *substrings: str):
        __tracebackhide__ = True
        embed = await self.dispatch_msg_get_embeds(msg, only_one=True)
        super().assert_error(embed, *substrings)

    # region Get user's timezone

    async def test_basic(self):
        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            "do you guys wanna play at {9pm}?",
            r'Europe/Amsterdam.+9:00 PM',
            r'Europe/London.+8:00 PM',
            r'America/New_York.+3:00 PM'
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "I get off work at {330pm}",
            r'Europe/Amsterdam.+9:30 PM',
            r'Europe/London.+8:30 PM',
            r'America/New_York.+3:30 PM'
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "In 24-hour time that's {1530}",
            r'Europe/Amsterdam.+9:30 PM',
            r'Europe/London.+8:30 PM',
            r'America/New_York.+3:30 PM'
        )

        self.msg.author.id = self.british_user
        await self.assert_regex_reply(
            "yeah I've gotta wake up at {5} for work tomorrow, so it's an "
            "early bedtime for me",
            r'Europe/Amsterdam.+6:00 AM',
            r'Europe/London.+5:00 AM',
            r'America/New_York.+12:00 AM'
        )

    async def test_multiple(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "I wish I could, but I'm busy from {14} to {17:45}",
            r'Europe/Amsterdam.+8:00 PM.+11:45 PM',
            r'Europe/London.+7:00 PM.+10:45 PM',
            r'America/New_York.+2:00 PM.+5:45 PM'
        )

    async def test_keyword(self):
        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            "It's nearly {noon}. Time for lunch!",
            r'Europe/Amsterdam.+12:00 PM',
            r'Europe/London.+11:00 AM',
            r'America/New_York.+6:00 AM'
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "Dude, it's {midnight} :gobed:!",
            r'Europe/Amsterdam.+6:00 AM',
            r'Europe/London.+5:00 AM',
            r'America/New_York.+12:00 AM'
        )

    async def test_now(self):
        self.msg.author.id = self.british_user
        await self.assert_regex_reply(
            "I'm free {now}, anyone want to do something?",
            r'Europe/Amsterdam.+' + self.dutch_now.strftime("%I:%M %p").lstrip("0"),
            r'Europe/London.+' + self.british_now.strftime("%I:%M %p").lstrip("0"),
            r'America/New_York.+' + self.american_now.strftime("%I:%M %p").lstrip("0")
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "I'm free {now}, anyone want to do something?",
            r'Europe/Amsterdam.+' + self.dutch_now.strftime("%I:%M %p").lstrip("0"),
            r'Europe/London.+' + self.british_now.strftime("%I:%M %p").lstrip("0"),
            r'America/New_York.+' + self.american_now.strftime("%I:%M %p").lstrip("0")
        )

    # endregion

    # region Specified input timezone

    async def test_in_basic(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "Jaakko's getting on at {8 pm helsinki}",
            r'Europe/Amsterdam.+7:00 PM',
            r'Europe/London.+6:00 PM',
            r'America/New_York.+1:00 PM'
        )

        self.msg.author.id = self.british_user
        await self.assert_regex_reply(
            "aka {8pm helsinki}",
            r'Europe/Amsterdam.+7:00 PM',
            r'Europe/London.+6:00 PM',
            r'America/New_York.+1:00 PM'
        )

        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            "aka {20:00 helsinki}",
            r'Europe/Amsterdam.+7:00 PM',
            r'Europe/London.+6:00 PM',
            r'America/New_York.+1:00 PM'
        )

    async def test_in_multiple(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "my flight took off at {7pm new york} and landed at {8 AM london}",
            r'Europe/Amsterdam.+1:00 AM.+9:00 AM',
            r'Europe/London.+12:00 AM.+8:00 AM',
            r'America/New_York.+7:00 PM.+3:00 AM'
        )

    async def test_in_keyword(self):
        self.msg.author.id = self.british_user
        await self.assert_regex_reply(
            "he's getting lunch around {noon los angeles}",
            r'Europe/Amsterdam.+9:00 PM',
            r'Europe/London.+8:00 PM',
            r'America/New_York.+3:00 PM'
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "My flight's landing at {midnight brussels}",
            r'Europe/Amsterdam.+12:00 AM',
            r'Europe/London.+11:00 PM',
            r'America/New_York.+6:00 PM'
        )

    async def test_in_now(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "{now amsterdam} is redundant but it shouldn't fail",
            r'Europe/Amsterdam.+11:32 AM',
            r'Europe/London.+10:32 AM',
            r'America/New_York.+5:32 AM'
        )

    async def test_in_ambiguous_with_unit(self):
        self.msg.author.id = self.american_user
        await self.assert_error(
            "{20 helsinki} (8:00 pm Helsinki time) isn't allowed because it's "
            "ambiguous with a unit 'helsinki' with magnitude 20. You must add "
            "AM/PM or use a colon.",

            'Unknown unit "helsinki"',
        )

    async def test_in_unknown_timezone(self):
        self.msg.author.id = self.american_user
        await self.assert_error(
            "this don't exist {8:00 ZBNMBSAEFHJBGEWB}",
            'Timezone "ZBNMBSAEFHJBGEWB" not found'
        )

    # endregion

    # region Specified output timezone

    async def test_out_basic(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "alex, I'm gonna restart the server at {11 > amsterdam}",
            r'Europe/Amsterdam.+5:00 PM',
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "or I can wait until {8pm > amsterdam}",
            r'Europe/Amsterdam.+2:00 AM',
        )

    async def test_out_multiple(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "hey bruce I wanna show you something, I'm free between "
            "{11am > london} and {3 PM > Europe/London}",
            r'Europe/London.+4:00 PM.+8:00 PM',
        )

        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            "the game's releasing for americans at {1 PM > new york} and "
            "{1500 > london} for europeans"
            r'America/New_York.+7:00 AM',
            r'Europe/London.+2:00 PM',
        )

    async def test_out_keyword(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "the solar eclipse will be happening here while the hawaiians "
            "are sleeping! {noon > honolulu}",
            r'Pacific/Honolulu.+6:00 AM'
        )

        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "and while I'm sleeping, they'll be eating dinner "
            "{midnight > honolulu}",
            r'Pacific/Honolulu.+6:00 PM'
        )

    async def test_out_now(self):
        self.msg.author.id = self.american_user
        await self.assert_regex_reply(
            "what time is it in dubai? {now > dubai}",
            r'Asia/Dubai.+1:32 PM',
        )

    async def test_out_unknown_timezone(self):
        self.msg.author.id = self.american_user
        await self.assert_error(
            "no timezone {8:00 > ZBNMBSAEFHJBGEWB}",
            'Timezone "ZBNMBSAEFHJBGEWB" not found',
        )

    async def test_out_empty(self):
        self.msg.author.id = self.american_user
        await self.assert_no_reply("no timezone {8:00 > }")

    # endregion

    # region Specified input and output timezone

    async def test_in_out_basic(self):
        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            "I've run out of interesting message ideas "
            "{5:00 pm honolulu > los angeles}",

            r'America/Los_Angeles.+8:00 PM',
        )

    async def test_in_out_multiple(self):
        self.msg.author.id = self.british_user
        await self.assert_regex_reply(
            "you probably get the idea by now "
            "{5:00 pm honolulu > los angeles} and also "
            "{10:00 amsterdam > london} annnd back to "
            "{1am new york > los angeles}",

            r'America/Los_Angeles.+8:00 PM.+10:00 PM',
            r'Europe/London.+9:00 AM',
        )

    async def test_in_out_keyword(self):
        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            ":) {midnight los angeles > honolulu}",
            r'Pacific/Honolulu.+9:00 PM',
        )

        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            ":D {noon london > new york}",
            r'America/New_York.+7:00 AM',
        )

    async def test_in_out_now(self):
        self.msg.author.id = self.dutch_user
        await self.assert_regex_reply(
            ":O {now new york > amsterdam}",
            r'Europe/Amsterdam.+11:32 AM',
        )

    async def test_in_out_unknown_timezone(self):
        self.msg.author.id = self.dutch_user
        await self.assert_error(
            ":( {10 amsterdam > london}",
            'Unknown unit "amsterdam"',
        )

    # endregion
