import datetime as dt
import unittest.mock as mock

import discord.ext.commands as commands
import pytz

from ._test_helpers import DiscordMockingTestCase
from sandpiper.bios import Bios
from sandpiper.user_data.database_sqlite import DatabaseSQLite
from sandpiper.user_data.enums import PrivacyType

__all__ = ['TestBios']

CONNECTION = ':memory:'


class TestBios(DiscordMockingTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()

        # Connect to a dummy database
        self.db = DatabaseSQLite(CONNECTION)
        await self.db.connect()

        # Bypass UserData cog lookup by patching in the database
        patcher = mock.patch(
            'sandpiper.bios.Bios._get_database',
            return_value=self.db
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        await self.db.disconnect()

    def setup_cogs(self, bot: commands.Bot):
        self.bios = Bios(bot)
        bot.add_cog(self.bios)

    async def make_greg(self, user_id: int):
        await self.db.set_preferred_name(user_id, 'Greg')
        await self.db.set_pronouns(user_id, 'He/Him')
        await self.db.set_birthday(user_id, dt.date(2000, 2, 14))
        await self.db.set_timezone(user_id, pytz.timezone('America/New_York'))

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

        # Individual

        embeds = await self.invoke_cmd_get_embeds('privacy name public')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy pronouns public')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy birthday public')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy age public')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy timezone public')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PUBLIC)

        embeds = await self.invoke_cmd_get_embeds('privacy name private')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy pronouns private')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy birthday private')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy age private')
        self.assert_success(embeds[0])
        embeds = await self.invoke_cmd_get_embeds('privacy timezone private')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PRIVATE)

        # Batch set

        embeds = await self.invoke_cmd_get_embeds('privacy all public')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PUBLIC)

        embeds = await self.invoke_cmd_get_embeds('privacy all private')
        self.assert_success(embeds[0])
        await assert_all_privacies(PrivacyType.PRIVATE)

    async def test_show(self):
        uid = 123
        self.msg.author.id = uid
        self.msg.guild = None

        await self.make_greg(uid)

        # Individual

        embeds = await self.invoke_cmd_get_embeds('name show')
        self.assert_info(embeds[0], 'Greg')

        embeds = await self.invoke_cmd_get_embeds('pronouns show')
        self.assert_info(embeds[0], 'He/Him')

        embeds = await self.invoke_cmd_get_embeds('birthday show')
        self.assert_info(embeds[0], '2000-02-14')

        embeds = await self.invoke_cmd_get_embeds('age show')
        self.assert_info(embeds[0])
        self.assertRegex(embeds[0].description, r'\d+')

        embeds = await self.invoke_cmd_get_embeds('timezone show')
        self.assert_info(embeds[0], 'America/New_York')

        # Batch show

        embeds = await self.invoke_cmd_get_embeds('bio show')
        self.assert_info(embeds[0], 'Greg')
        self.assert_info(embeds[0], 'He/Him')
        self.assert_info(embeds[0], '2000-02-14')
        self.assert_info(embeds[0], 'America/New_York')

    async def test_set(self):
        uid = 123
        self.msg.author.id = uid
        self.msg.guild = None

        # Success

        embeds = await self.invoke_cmd_get_embeds('name set Greg')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy name public')
        value = await self.db.get_preferred_name(uid)
        self.assertEqual(value, 'Greg')

        embeds = await self.invoke_cmd_get_embeds('pronouns set He/Him')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy pronouns public')
        value = await self.db.get_pronouns(uid)
        self.assertEqual(value, 'He/Him')

        embeds = await self.invoke_cmd_get_embeds('birthday set 2000-02-14')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy birthday public')
        value = await self.db.get_birthday(uid)
        self.assertEqual(value, dt.date(2000, 2, 14))

        embeds = await self.invoke_cmd_get_embeds('age set 20')
        self.assert_error(embeds[0])

        embeds = await self.invoke_cmd_get_embeds('timezone set new york')
        self.assert_success(embeds[0])
        self.assert_warning(embeds[1], 'privacy timezone public')
        value = await self.db.get_timezone(uid)
        self.assertEqual(value, pytz.timezone('America/New_York'))

        # Errors

        with self.assertRaisesRegex(commands.BadArgument, r'64 characters'):
            await self.invoke_cmd_get_embeds('name set ' + 'a'*65)

        with self.assertRaisesRegex(commands.BadArgument, r'64 characters'):
            await self.invoke_cmd_get_embeds('pronouns set ' + 'a'*65)

    async def test_delete(self):
        uid = 123
        self.msg.author.id = uid
        self.msg.guild = None

        await self.make_greg(uid)

        # Individual

        embeds = await self.invoke_cmd_get_embeds('name delete')
        self.assert_success(embeds[0])
        self.assertIsNone(await self.db.get_preferred_name(uid))

        embeds = await self.invoke_cmd_get_embeds('pronouns delete')
        self.assert_success(embeds[0])
        self.assertIsNone(await self.db.get_pronouns(uid))

        embeds = await self.invoke_cmd_get_embeds('age delete')
        self.assert_error(embeds[0], 'birthday delete')

        embeds = await self.invoke_cmd_get_embeds('birthday delete')
        self.assert_success(embeds[0])
        self.assertIsNone(await self.db.get_birthday(uid))
        self.assertIsNone(await self.db.get_age(uid))

        embeds = await self.invoke_cmd_get_embeds('timezone delete')
        self.assert_success(embeds[0])
        self.assertIsNone(await self.db.get_timezone(uid))

        # Batch delete

        await self.make_greg(uid)
        embeds = await self.invoke_cmd_get_embeds('bio delete')
        self.assert_success(embeds[0])
        self.assertIsNone(await self.db.get_preferred_name(uid))
        self.assertIsNone(await self.db.get_pronouns(uid))
        self.assertIsNone(await self.db.get_birthday(uid))
        self.assertIsNone(await self.db.get_age(uid))
        self.assertIsNone(await self.db.get_timezone(uid))
