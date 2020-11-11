import datetime as dt
import unittest.mock as mock

import discord.ext.commands as commands
import pytz

from ._test_helpers import *
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

    # noinspection DuplicatedCode
    async def test_whois(self):

        db = self.db

        # Guild 0
        # Should be visible in guild and DMs

        self.add_guild(0)

        executor = self.add_user(0, 'Executor')
        self.add_user_to_guild(0, 0, '_executor_'),

        # Test username
        self.add_user(1001, 'Greg')
        self.add_user_to_guild(0, 1001, '_blank_'),
        await db.set_preferred_name(1001, '*Blank*')
        await db.set_privacy_preferred_name(1001, PrivacyType.PUBLIC)

        # Test display name
        self.add_user(1002, 'Blank')
        self.add_user_to_guild(0, 1002, '_greg_'),
        await db.set_preferred_name(1002, '*Blank*')
        await db.set_privacy_preferred_name(1002, PrivacyType.PUBLIC)

        # Test preferred name
        self.add_user(1003, 'Blank')
        self.add_user_to_guild(0, 1003, '_blank_'),
        await db.set_preferred_name(1003, '*Greg*')
        await db.set_privacy_preferred_name(1003, PrivacyType.PUBLIC)

        # Test display name constriction to guild
        self.add_user(1004, 'Blank')
        self.add_user_to_guild(0, 1004, '_greg_'),
        await db.set_preferred_name(1004, '*Blank*')
        await db.set_privacy_preferred_name(1004, PrivacyType.PUBLIC)

        # Test pronouns
        self.add_user(1005, 'Blank')
        self.add_user_to_guild(0, 1005, '_blank_'),
        await db.set_preferred_name(1005, '*Greg*')
        await db.set_privacy_preferred_name(1005, PrivacyType.PUBLIC)
        await db.set_pronouns(1005, 'He/Him')
        await db.set_privacy_pronouns(1005, PrivacyType.PUBLIC)

        # Test lack of preferred name
        self.add_user(1006, 'Greg')
        self.add_user_to_guild(0, 1006, '_blank_'),
        await db.set_preferred_name(1006, None)
        await db.set_privacy_preferred_name(1006, PrivacyType.PRIVATE)

        # Guild 1
        # Should only be visible in DMs

        self.add_guild(1)

        self.add_user_to_guild(1, 0, '_executor_'),
        # Test duplicate removal
        self.add_user_to_guild(1, 1001, '_GregDuplicate_'),
        # Test display names from multiple guilds
        self.add_user_to_guild(1, 1004, '_extra_nickname_'),

        # Test username
        self.add_user(2001, 'GuildHiddenGreg')
        self.add_user_to_guild(1, 2001, '_blank_'),
        await db.set_preferred_name(2001, '*Blank*')
        await db.set_privacy_preferred_name(2001, PrivacyType.PUBLIC)

        # Test display name
        self.add_user(2002, 'Blank')
        self.add_user_to_guild(1, 2002, '_guildhiddengreg_'),
        await db.set_preferred_name(2002, '*Blank*')
        await db.set_privacy_preferred_name(2002, PrivacyType.PUBLIC)

        # Test preferred name
        self.add_user(2003, 'Blank')
        self.add_user_to_guild(1, 2003, '_blank_'),
        await db.set_preferred_name(2003, '*GuildHiddenGreg*')
        await db.set_privacy_preferred_name(2003, PrivacyType.PUBLIC)

        # Guild 2
        # Should be totally hidden

        self.add_guild(2)

        # Test username
        self.add_user(3001, 'TotallyHiddenGreg')
        self.add_user_to_guild(2, 3001, '_blank_'),
        await db.set_preferred_name(3001, '*Blank*')
        await db.set_privacy_preferred_name(3001, PrivacyType.PUBLIC)

        # Test display name
        self.add_user(3002, 'Blank')
        self.add_user_to_guild(2, 3002, '_totallyhiddengreg_'),
        await db.set_preferred_name(3002, '*Blank*')
        await db.set_privacy_preferred_name(3002, PrivacyType.PUBLIC)

        # Test preferred name
        self.add_user(3003, 'Blank')
        self.add_user_to_guild(2, 3003, '_blank_'),
        await db.set_preferred_name(3003, '*TotallyHiddenGreg*')
        await db.set_privacy_preferred_name(3003, PrivacyType.PUBLIC)

        # Finish setup

        self.msg.author = executor

        # Invoke in a guild

        self.msg.guild = self.guilds_map[0]

        embeds = await self.invoke_cmd_get_embeds("whois greg")
        self.assert_info(embeds[0])
        desc: str = embeds[0].description
        self.assertIn("*Blank* • Greg#1001 • _blank_", desc)
        self.assertIn("*Blank* • Blank#1002 • _greg_", desc)
        self.assertIn("*Greg* • Blank#1003 • _blank_", desc)
        self.assertIn("*Blank* • Blank#1004 • _greg_", desc)
        self.assertIn("*Greg* (He/Him) • Blank#1005 • _blank_", desc)
        self.assertIn("`No preferred name` • Greg#1006 • _blank_", desc)

        self.assertNotIn("_extra_nickname_", desc)
        self.assertNotIn("GuildHiddenGreg#2001", desc)
        self.assertNotIn("Blank#2002", desc)
        self.assertNotIn("Blank#2003", desc)

        self.assertNotIn("TotallyHiddenGreg#3001", desc)
        self.assertNotIn("Blank#3002", desc)
        self.assertNotIn("Blank#3003", desc)

        # Invoke in DMs

        self.msg.guild = None

        embeds = await self.invoke_cmd_get_embeds('whois greg')
        self.assert_info(embeds[0])
        desc: str = embeds[0].description
        self.assertIn("*Greg* • Blank#1003 • _blank_", desc)
        self.assertIn("*Greg* (He/Him) • Blank#1005 • _blank_", desc)
        self.assertIn("*Blank* • Greg#1001 • _blank_", desc)
        self.assertEqual(desc.count('Greg#1001'), 1)
        self.assertIn("*Blank* • Blank#1002 • _greg_", desc)
        self.assertIn("*Blank* • Blank#1004 • _greg_, _extra_nickname_", desc)
        self.assertIn("`No preferred name` • Greg#1006 • _blank_", desc)

        self.assertIn("*Blank* • GuildHiddenGreg#2001 • _blank_", desc)
        self.assertIn("*Blank* • Blank#2002 • _guildhiddengreg_", desc)
        self.assertIn("*GuildHiddenGreg* • Blank#2003 • _blank_", desc)

        self.assertNotIn("TotallyHiddenGreg#3001", desc)
        self.assertNotIn("Blank#3002", desc)
        self.assertNotIn("Blank#3003", desc)

        # Erroring commands

        embeds = await self.invoke_cmd_get_embeds("whois gregothy")
        self.assert_error(embeds[0], "No users")

        with self.assertRaises(commands.BadArgument):
            await self.invoke_cmd_get_embeds("whois e")
