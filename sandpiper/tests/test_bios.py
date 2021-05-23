from collections.abc import Awaitable, Callable
import datetime as dt
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytest
import pytz

from ._helpers import *
from sandpiper.bios import Bios
from sandpiper.user_data.database_sqlite import DatabaseSQLite
from sandpiper.user_data.enums import PrivacyType

__all__ = (
    'TestPrivacy', 'TestShow', 'TestSet', 'TestDelete', 'TestWhois'
)

pytestmark = pytest.mark.asyncio

T_DatabaseMethod = Callable[[int], Awaitable[PrivacyType]]


@pytest.fixture()
async def database() -> DatabaseSQLite:
    """Create, connect, and patch in a database adapter."""

    # Connect to a dummy database
    db = DatabaseSQLite(':memory:')
    await db.connect()

    # Bypass UserData cog lookup by patching in the database
    patcher = mock.patch('sandpiper.bios.Bios._get_database', return_value=db)
    patcher.start()

    yield db

    await db.disconnect()
    patcher.stop()


@pytest.fixture()
def bios_bot(bot) -> Bios:
    """Add a Bios cog to a bot and return the cog"""
    bios = Bios(bot)
    bot.add_cog(bios)
    return bios


@pytest.fixture()
async def greg(database, user_id) -> int:
    """Make a dummy 'Greg' user in the database and return his user ID"""
    await database.set_preferred_name(user_id, 'Greg')
    await database.set_pronouns(user_id, 'He/Him')
    await database.set_birthday(user_id, dt.date(2000, 2, 14))
    await database.set_timezone(user_id, pytz.timezone('America/New_York'))
    return user_id


@pytest.fixture()
async def invoke_as_greg(message, greg):
    message.author.id = greg


@pytest.fixture()
def apply_new_user_id(new_id, message):
    id_ = new_id()
    message.author.id = new_id()
    return id_


@pytest.mark.usefixtures('apply_new_user_id')
class TestPrivacy:

    @staticmethod
    async def _assert(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod, privacy: PrivacyType
    ):
        __tracebackhide__ = True
        assert_success(embeds)
        assert await db_meth(message.author.id) is privacy

    @staticmethod
    async def _assert_all(
            embeds: list[discord.Embed], message: discord.Message,
            db: DatabaseSQLite, privacy: PrivacyType
    ):
        __tracebackhide__ = True
        assert_success(embeds)
        uid = message.author.id
        assert await db.get_privacy_preferred_name(uid) is privacy
        assert await db.get_privacy_pronouns(uid) is privacy
        assert await db.get_privacy_birthday(uid) is privacy
        assert await db.get_privacy_age(uid) is privacy
        assert await db.get_privacy_timezone(uid) is privacy

    # region Name

    async def test_name_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy name public')
        await self._assert(
            embeds, message, database.get_privacy_preferred_name,
            PrivacyType.PUBLIC
        )

    async def test_name_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy name private')
        await self._assert(
            embeds, message, database.get_privacy_preferred_name,
            PrivacyType.PRIVATE
        )

    async def test_name_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy name private')
        await self._assert(
            embeds, message, database.get_privacy_preferred_name,
            PrivacyType.PRIVATE
        )

        embeds = await invoke_cmd_get_embeds('privacy name public')
        await self._assert(
            embeds, message, database.get_privacy_preferred_name,
            PrivacyType.PUBLIC
        )

        embeds = await invoke_cmd_get_embeds('privacy name private')
        await self._assert(
            embeds, message, database.get_privacy_preferred_name,
            PrivacyType.PRIVATE
        )

    # endregion
    # region Pronouns

    async def test_pronouns_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy pronouns public')
        await self._assert(
            embeds, message, database.get_privacy_pronouns, PrivacyType.PUBLIC
        )

    async def test_pronouns_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy pronouns private')
        await self._assert(
            embeds, message, database.get_privacy_pronouns, PrivacyType.PRIVATE
        )

    async def test_pronouns_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy pronouns private')
        await self._assert(
            embeds, message, database.get_privacy_pronouns, PrivacyType.PRIVATE
        )

        embeds = await invoke_cmd_get_embeds('privacy pronouns public')
        await self._assert(
            embeds, message, database.get_privacy_pronouns, PrivacyType.PUBLIC
        )

        embeds = await invoke_cmd_get_embeds('privacy pronouns private')
        await self._assert(
            embeds, message, database.get_privacy_pronouns, PrivacyType.PRIVATE
        )

    # endregion
    # region Birthday

    async def test_birthday_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy birthday public')
        await self._assert(
            embeds, message, database.get_privacy_birthday, PrivacyType.PUBLIC
        )

    async def test_birthday_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy birthday private')
        await self._assert(
            embeds, message, database.get_privacy_birthday, PrivacyType.PRIVATE
        )

    async def test_birthday_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy birthday private')
        await self._assert(
            embeds, message, database.get_privacy_birthday, PrivacyType.PRIVATE
        )

        embeds = await invoke_cmd_get_embeds('privacy birthday public')
        await self._assert(
            embeds, message, database.get_privacy_birthday, PrivacyType.PUBLIC
        )

        embeds = await invoke_cmd_get_embeds('privacy birthday private')
        await self._assert(
            embeds, message, database.get_privacy_birthday, PrivacyType.PRIVATE
        )

    # endregion
    # region Age

    async def test_age_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy age public')
        await self._assert(
            embeds, message, database.get_privacy_age, PrivacyType.PUBLIC
        )

    async def test_age_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy age private')
        await self._assert(
            embeds, message, database.get_privacy_age, PrivacyType.PRIVATE
        )

    async def test_age_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy age private')
        await self._assert(
            embeds, message, database.get_privacy_age, PrivacyType.PRIVATE
        )

        embeds = await invoke_cmd_get_embeds('privacy age public')
        await self._assert(
            embeds, message, database.get_privacy_age, PrivacyType.PUBLIC
        )

        embeds = await invoke_cmd_get_embeds('privacy age private')
        await self._assert(
            embeds, message, database.get_privacy_age, PrivacyType.PRIVATE
        )

    # endregion
    # region Timezone

    async def test_timezone_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy timezone public')
        await self._assert(
            embeds, message, database.get_privacy_timezone, PrivacyType.PUBLIC
        )

    async def test_timezone_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy timezone private')
        await self._assert(
            embeds, message, database.get_privacy_timezone, PrivacyType.PRIVATE
        )

    async def test_timezone_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy timezone private')
        await self._assert(
            embeds, message, database.get_privacy_timezone, PrivacyType.PRIVATE
        )

        embeds = await invoke_cmd_get_embeds('privacy timezone public')
        await self._assert(
            embeds, message, database.get_privacy_timezone, PrivacyType.PUBLIC
        )

        embeds = await invoke_cmd_get_embeds('privacy timezone private')
        await self._assert(
            embeds, message, database.get_privacy_timezone, PrivacyType.PRIVATE
        )

    # endregion
    # region All

    async def test_all_public(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy all public')
        await self._assert_all(embeds, message, database, PrivacyType.PUBLIC)

    async def test_all_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy all private')
        await self._assert_all(embeds, message, database, PrivacyType.PRIVATE)

    async def test_all_cycle(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('privacy all private')
        await self._assert_all(embeds, message, database, PrivacyType.PRIVATE)
        embeds = await invoke_cmd_get_embeds('privacy all public')
        await self._assert_all(embeds, message, database, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds('privacy all private')
        await self._assert_all(embeds, message, database, PrivacyType.PRIVATE)

    # endregion


class TestShow:

    async def test_name(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('name show')
        assert_info(embeds, 'Greg')

    async def test_pronouns(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('pronouns show')
        assert_info(embeds, 'He/Him')

    async def test_birthday(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('birthday show')
        assert_info(embeds, '2000-02-14')

    @pytest.mark.skip("Need to patch in some datetime stuff")
    async def test_age(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('age show')
        assert_info(embeds, 'TODO')

    async def test_timezone(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('timezone show')
        assert_info(embeds, 'America/New_York')

    @pytest.mark.skip("Need to patch in some datetime stuff")
    async def test_all(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('bio show')
        assert_info(
            embeds,
            'Greg', 'He/Him', '2000-02-14', 'AGE TODO', 'America/New_York'
        )


class TestSet:

    @staticmethod
    async def _assert_private(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod, expected_value, privacy_field_name: str
    ):
        assert len(embeds) == 2
        assert_success(embeds[0])
        assert_warning(embeds[1], f'privacy {privacy_field_name} public')
        value = await db_meth(message.author.id)
        assert value == expected_value

    @staticmethod
    async def _assert_public(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod, expected_value
    ):
        assert len(embeds) == 1
        assert_success(embeds[0])
        value = await db_meth(message.author.id)
        assert value == expected_value

    # region Name

    async def test_name_private(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'name set Greg')
        await self._assert_private(
            embeds, message, database.get_preferred_name, 'Greg', 'name'
        )

    async def test_name_public(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'name set Greg')
        await self._assert_public(
            embeds, message, database.get_preferred_name, 'Greg'
        )

    async def test_name_too_long_err(self, invoke_cmd_get_embeds):
        with pytest.raises(commands.BadArgument, match='64 characters'):
            await invoke_cmd_get_embeds('name set ' + 'a'*65)

    # endregion
    # region Pronouns

    async def test_pronouns_private(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'pronouns set He/Him')
        await self._assert_private(
            embeds, message, database.get_pronouns, 'He/Him', 'pronouns'
        )

    async def test_pronouns_public(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'pronouns set He/Him')
        await self._assert_public(
            embeds, message, database.get_pronouns, 'He/Him'
        )

    async def test_pronouns_too_long_err(self, invoke_cmd_get_embeds):
        with pytest.raises(commands.BadArgument, match='64 characters'):
            await invoke_cmd_get_embeds('pronouns set ' + 'a'*65)

    # endregion
    # region Birthday

    async def test_birthday_private(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'birthday set 2000-02-14')
        await self._assert_private(
            embeds, message, database.get_birthday, dt.date(2000, 2, 14),
            'birthday'
        )

    async def test_birthday_public(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'birthday set 2000-02-14')
        await self._assert_public(
            embeds, message, database.get_birthday, dt.date(2000, 2, 14)
        )

    # endregion
    # region Age

    async def test_age(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'age set 20')
        assert_error(embeds)

    # endregion
    # region Timezone

    async def test_timezone_private(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'timezone set new york')
        await self._assert_private(
            embeds, message, database.get_timezone,
            pytz.timezone('America/New_York'), 'timezone'
        )

    async def test_timezone_public(self, database, message, invoke_cmd_get_embeds):
        embeds = invoke_cmd_get_embeds(f'timezone set new york')
        await self._assert_public(
            embeds, message, database.get_timezone,
            pytz.timezone('America/New_York')
        )

    # endregion


class TestDelete:

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


class TestWhois:

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
