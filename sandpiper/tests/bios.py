import datetime as dt
import unittest.mock as mock
from typing import *

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

        def id_getter(container: Iterable):
            def get(id: int):
                for i in container:
                    if i.id == id:
                        return i
                return None
            return get

        users = [
            MagicMock_(id=0, name='Executor', discriminator=0),
            MagicMock_(id=1111, name='Blank', discriminator=1111),
            MagicMock_(id=2222, name='Blank', discriminator=2222),
            MagicMock_(id=3333, name='Greg', discriminator=3333),
            MagicMock_(id=4444, name='Blank', discriminator=4444),
            MagicMock_(id=5555, name='Blank', discriminator=5555),
            MagicMock_(id=6666, name='Greg', discriminator=6666),
            MagicMock_(id=7777, name='GuildHiddenGreg', discriminator=7777),
            MagicMock_(id=8888, name='TotallyHiddenGreg', discriminator=8888),
            MagicMock_(id=9999, name='Blank', discriminator=9999),
        ]

        patcher = mock.patch.object(self.bot, 'get_user')
        get_user = patcher.start()
        get_user.side_effect = id_getter(users)
        self.addCleanup(patcher.stop)

        member_groups = [
            [
                MagicMock_(id=0, name='Executor', discriminator=0, display_name='_executor_'),
                MagicMock_(id=1111, name='Blank', discriminator=1111, display_name='_blank_'),
                MagicMock_(id=2222, name='Blank', discriminator=2222, display_name='_blank_'),
                MagicMock_(id=3333, name='Greg', discriminator=3333, display_name='_blank_'),
                MagicMock_(id=4444, name='Blank', discriminator=4444, display_name='_greg_'),
                MagicMock_(id=5555, name='Blank', discriminator=5555, display_name='_greg_'),
                MagicMock_(id=6666, name='Greg', discriminator=6666, display_name='_blank_'),
            ],
            [
                MagicMock_(id=0, name='Executor', discriminator=0, display_name='_executor_'),
                MagicMock_(id=5555, name='Blank', discriminator=5555, display_name='another nickname'),
                MagicMock_(id=7777, name='GuildHiddenGreg', discriminator=7777, display_name='_guildhiddengreg_'),
            ],
            [
                MagicMock_(id=8888, name='TotallyHiddenGreg', discriminator=8888, display_name='_blank_'),
                MagicMock_(id=9999, name='Blank', discriminator=9999, display_name='_totallyhiddengreg_'),
            ]
        ]

        guilds = []
        for members in member_groups:
            guild = mock.MagicMock()
            guild.members = members
            guild.get_member.side_effect = id_getter(members)
            guilds.append(guild)

        db = self.db
        await db.set_preferred_name(1111, '*Greg*')
        await db.set_preferred_name(2222, '*Greg*')
        await db.set_preferred_name(3333, '*Blank*')
        await db.set_preferred_name(4444, '*Blank*')
        await db.set_preferred_name(5555, '*Blank*')
        await db.set_preferred_name(6666, None)
        await db.set_preferred_name(7777, '*GuildHiddenGreg*')
        await db.set_privacy_preferred_name(1111, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(2222, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(3333, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(4444, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(5555, PrivacyType.PUBLIC)
        await db.set_privacy_preferred_name(6666, PrivacyType.PRIVATE)
        await db.set_privacy_preferred_name(7777, PrivacyType.PUBLIC)
        await db.set_pronouns(2222, 'He/Him')
        await db.set_privacy_pronouns(2222, PrivacyType.PUBLIC)

        self.bot.guilds = guilds
        self.bot.users = users
        self.msg.author = users[0]

        # Invoke in a guild
        self.msg.guild = guilds[0]

        embeds = await self.invoke_cmd_get_embeds('whois greg')
        self.assert_info(embeds[0])
        desc = embeds[0].description
        self.assertIn("*Greg* • Blank#1111 • _blank_", desc)
        self.assertIn("*Greg* (He/Him) • Blank#2222 • _blank_", desc)
        self.assertIn("*Blank* • Greg#3333 • _blank_", desc)
        self.assertIn("*Blank* • Blank#4444 • _greg_", desc)
        self.assertIn("*Blank* • Blank#5555 • _greg_", desc)
        self.assertIn("`No preferred name` • Greg#6666 • _blank_", desc)
        self.assertNotIn('GuildHiddenGreg#7777', desc)
        self.assertNotIn('TotallyHiddenGreg#8888', desc)
        self.assertNotIn('_totallyhiddengreg_', desc)

        # Invoke in DMs
        self.msg.guild = None

        embeds = await self.invoke_cmd_get_embeds('whois greg')
        self.assert_info(embeds[0])
        desc = embeds[0].description
        self.assertIn("*Greg* • Blank#1111 • _blank_", desc)
        self.assertIn("*Greg* (He/Him) • Blank#2222 • _blank_", desc)
        self.assertIn("*Blank* • Greg#3333 • _blank_", desc)
        self.assertIn("*Blank* • Blank#4444 • _greg_", desc)
        self.assertIn("*Blank* • Blank#5555 • _greg_, another nickname", desc)
        self.assertIn("`No preferred name` • Greg#6666 • _blank_", desc)
        self.assertIn('*GuildHiddenGreg* • GuildHiddenGreg#7777 • _guildhiddengreg_', desc)
        self.assertNotIn('TotallyHiddenGreg#8888', desc)
        self.assertNotIn('_totallyhiddengreg_', desc)

        # Erroring commands

        embeds = await self.invoke_cmd_get_embeds('whois gregothy')
        self.assert_error(embeds[0], "No users")

        with self.assertRaises(commands.BadArgument):
            await self.invoke_cmd_get_embeds('whois e')
