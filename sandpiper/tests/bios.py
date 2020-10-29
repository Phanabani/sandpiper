import datetime as dt
import unittest
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytz

from sandpiper.bios import Bios
from sandpiper.user_info.database_sqlite import DatabaseSQLite

__all__ = ['TestBios']

CONNECTION = ':memory:'


class TestBios(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self._db = DatabaseSQLite(CONNECTION)
        await self._db.connect()

        patcher = mock.patch(
            'sandpiper.bios.Bios._get_database',
            return_value=self._db
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        Bot = mock.create_autospec(commands.Bot)
        Context = mock.create_autospec(commands.Context)
        bot = Bot(command_prefix='')
        self._bios = Bios(bot)
        self._ctx = Context()

    async def asyncTearDown(self) -> None:
        await self._db.disconnect()

    async def test_show(self):
        uid = 123
        self._ctx.author.id = uid
        await self._db.set_preferred_name(uid, 'Greg')
        await self._db.set_pronouns(uid, 'He/Him')
        await self._db.set_birthday(uid, dt.date(2000, 2, 14))
        await self._db.set_timezone(uid, pytz.timezone('America/New_York'))

        await self._bios.name_show.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertIn('Greg', embed.description)

        await self._bios.pronouns_show.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertIn('He/Him', embed.description)

        await self._bios.birthday_show.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertIn('2000-02-14', embed.description)

        await self._bios.age_show.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertRegex(embed.description, r'\d+')

        await self._bios.timezone_show.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertIn('America/New_York', embed.description)

    async def test_set(self):
        uid = 123
        self._ctx.author.id = uid

        await self._bios.name_set.callback(self._bios, self._ctx, 'Greg')
        value = await self._db.get_preferred_name(uid)
        self.assertEqual(value, 'Greg')

        await self._bios.pronouns_set.callback(self._bios, self._ctx, 'He/Him')
        value = await self._db.get_pronouns(uid)
        self.assertEqual(value, 'He/Him')

        await self._bios.birthday_set.callback(self._bios, self._ctx, '2000-02-14')
        value = await self._db.get_birthday(uid)
        self.assertEqual(value, dt.date(2000, 2, 14))

        await self._bios.age_set.callback(self._bios, self._ctx)
        embed: discord.Embed = self._ctx.send.call_args.kwargs['embed']
        self.assertIn('Error', embed.title)

        await self._bios.timezone_set.callback(self._bios, self._ctx, new_timezone='America/New_York')
        value = await self._db.get_timezone(uid)
        self.assertEqual(value, pytz.timezone('America/New_York'))
