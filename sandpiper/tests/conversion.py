import discord.ext.commands as commands

from ._test_helpers import DiscordMockingTestCase
from sandpiper.conversion.cog import Conversion

__all__ = ['TestConversion']


class TestConversion(DiscordMockingTestCase):

    def setup_cogs(self, bot: commands.Bot):
        bot.add_cog(Conversion(bot))

    async def test_unit_conversion(self):
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

    async def test_time_conversion(self):
        pass
