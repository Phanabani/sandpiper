import datetime as dt
from typing import List
import unittest
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytz

from sandpiper.bios import Bios
from sandpiper.user_info.database_sqlite import DatabaseSQLite
from sandpiper.user_info.enums import PrivacyType

__all__ = ['TestBios']

CONNECTION = ':memory:'


class TestBios(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
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

        # This is the meat of the operation; it allows for message properties
        # to be set where normally it is prohibited
        self.msg = mock.MagicMock(spec=discord.Message)
        self.msg.author.bot = False  # Otherwise the invocation will be skipped

        # Create a dummy bot that will never actually connect but will help
        # with invocation
        self.bot = commands.Bot(command_prefix='')
        self.bios = Bios(self.bot)
        self.bot.add_cog(self.bios)

        # This function checks if message author is the self bot and skips
        # context creation (meaning we won't get command invocation), so
        # we will bypass it
        patcher = mock.patch.object(self.bot, '_skip_check', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

        # This connection (discord.state.ConnectionState) object has a `user`
        # field which is accessed by the client's `user` property. The
        # _skip_check function is called with `client.user.id` which doesn't
        # exist (since we aren't connecting) and raises an AttributeError, so
        # we need to patch it in.
        patcher = mock.patch.object(self.bot, '_connection')
        connection_mock = patcher.start()
        connection_mock.user.id = 0
        self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        await self.db.disconnect()

    async def do_invoke(self, message_content: str) -> mock.AsyncMock:
        """
        Use self._msg to invoke a command.

        :returns: an AsyncMock representing the `ctx.send` method. You can use
            the methods defined in Mock to check the calls to this method by
            the command invocation.
        """
        self.msg.content = message_content
        ctx = await self.bot.get_context(self.msg)
        ctx.send = mock.AsyncMock()
        await self.bot.invoke(ctx)
        return ctx.send

    async def do_invoke_get_embeds(
            self, message_content: str) -> List[discord.Embed]:
        send = await self.do_invoke(message_content)
        return [
            embed for call in send.call_args_list
            if (embed := call.kwargs.get('embed'))
        ]

    # noinspection PyUnresolvedReferences
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
