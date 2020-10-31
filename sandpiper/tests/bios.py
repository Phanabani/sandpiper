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

    async def test_privacy(self):
        uid = 123
        self.msg.author.id = uid

        async def assert_all_privacies(privacy: PrivacyType):
            name = await self.db.get_privacy_preferred_name(uid)
            pronouns = await self.db.get_privacy_pronouns(uid)
            birthday = await self.db.get_privacy_birthday(uid)
            age = await self.db.get_privacy_age(uid)
            timezone = await self.db.get_privacy_timezone(uid)
            self.assertEqual(name, privacy)
            self.assertEqual(pronouns, privacy)
            self.assertEqual(birthday, privacy)
            self.assertEqual(age, privacy)
            self.assertEqual(timezone, privacy)

        embeds = await self.do_invoke_get_embeds('privacy name public')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy pronouns public')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy birthday public')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy age public')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy timezone public')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PUBLIC)

        embeds = await self.do_invoke_get_embeds('privacy name private')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy pronouns private')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy birthday private')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy age private')
        self.assert_success(embeds[0])
        embeds = await self.do_invoke_get_embeds('privacy timezone private')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PRIVATE)

        embeds = await self.do_invoke_get_embeds('privacy all public')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PUBLIC)

        embeds = await self.do_invoke_get_embeds('privacy all private')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PRIVATE)

    async def test_show(self):
        uid = 123
        self.msg.author.id = uid
        self.msg.guild = None

        await self.db.set_preferred_name(uid, 'Greg')
        await self.db.set_pronouns(uid, 'He/Him')
        await self.db.set_birthday(uid, dt.date(2000, 2, 14))
        await self.db.set_timezone(uid, pytz.timezone('America/New_York'))

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
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy name public')
        value = await self.db.get_preferred_name(uid)
        self.assertEqual(value, 'Greg')

        embeds = await self.do_invoke_get_embeds('pronouns set He/Him')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy pronouns public')
        value = await self.db.get_pronouns(uid)
        self.assertEqual(value, 'He/Him')

        embeds = await self.do_invoke_get_embeds('birthday set 2000-02-14')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy birthday public')
        value = await self.db.get_birthday(uid)
        self.assertEqual(value, dt.date(2000, 2, 14))

        embeds = await self.do_invoke_get_embeds('age set 20')
        self.assert_error(embeds[0])

        embeds = await self.do_invoke_get_embeds('timezone set new york')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy timezone public')
        value = await self.db.get_timezone(uid)
        self.assertEqual(value, pytz.timezone('America/New_York'))
