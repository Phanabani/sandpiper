import datetime as dt

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from sandpiper.bios import Bios
from sandpiper.user_info.enums import PrivacyType

__all__ = ['TestBios']


class TestBios(DiscordMockingTestCase):

    def setup_cogs(self, bot: commands.Bot):
        self.bios = Bios(bot)
        bot.add_cog(self.bios)

    async def test_show(self):
        uid = 123
        await self.db.set_preferred_name(uid, 'Greg')
        await self.db.set_pronouns(uid, 'He/Him')
        await self.db.set_birthday(uid, dt.date(2000, 2, 14))
        await self.db.set_timezone(uid, pytz.timezone('America/New_York'))

        self.msg.author.id = uid
        self.msg.guild = None

        embeds = await self.do_invoke_get_embeds('name show')
        self.assertIn('Greg', embeds[0].description)

        embeds = await self.do_invoke_get_embeds('pronouns show')
        self.assertIn('He/Him', embeds[0].description)

        embeds = await self.do_invoke_get_embeds('birthday show')
        self.assertIn('2000-02-14', embeds[0].description)

        embeds = await self.do_invoke_get_embeds('age show')
        self.assertRegex(embeds[0].description, r'\d+')

        embeds = await self.do_invoke_get_embeds('timezone show')
        self.assertIn('America/New_York', embeds[0].description)

    async def test_set(self):
        uid = 123
        self.msg.author.id = uid
        self.msg.guild = None

        embeds = await self.do_invoke_get_embeds('name set Greg')
        self.assertIn('Success', embeds[0].title)
        self.assertIn('Warning', embeds[1].title)
        self.assertIn('privacy name public', embeds[1].description)
        value = await self.db.get_preferred_name(uid)
        self.assertEqual(value, 'Greg')

        embeds = await self.do_invoke_get_embeds('pronouns set He/Him')
        self.assertIn('Success', embeds[0].title)
        self.assertIn('Warning', embeds[1].title)
        self.assertIn('privacy pronouns public', embeds[1].description)
        value = await self.db.get_pronouns(uid)
        self.assertEqual(value, 'He/Him')

        embeds = await self.do_invoke_get_embeds('birthday set 2000-02-14')
        self.assertIn('Success', embeds[0].title)
        self.assertIn('Warning', embeds[1].title)
        self.assertIn('privacy birthday public', embeds[1].description)
        value = await self.db.get_birthday(uid)
        self.assertEqual(value, dt.date(2000, 2, 14))

        embeds = await self.do_invoke_get_embeds('age set 20')
        self.assertIn('Error', embeds[0].title)

        embeds = await self.do_invoke_get_embeds('timezone set new york')
        self.assertIn('Success', embeds[0].title)
        self.assertIn('Warning', embeds[1].title)
        self.assertIn('privacy timezone public', embeds[1].description)
        value = await self.db.get_timezone(uid)
        self.assertEqual(value, pytz.timezone('America/New_York'))
