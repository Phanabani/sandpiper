from collections.abc import Awaitable, Callable
import datetime as dt
from typing import Optional
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytest
import pytz

from ._helpers import *
from sandpiper.bios import Bios
from sandpiper.user_data.database_sqlite import DatabaseSQLite
from sandpiper.user_data.enums import PrivacyType

pytestmark = pytest.mark.asyncio

T_DatabaseMethod = Callable[[int], Awaitable[PrivacyType]]


@pytest.fixture()
async def database() -> DatabaseSQLite:
    """Create, connect, and patch in a database adapter"""

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
def bot(bot) -> commands.Bot:
    """Add a Bios cog to a bot and return the bot"""
    bios = Bios(bot)
    bot.add_cog(bios)
    return bot


@pytest.fixture()
async def greg(database, new_id) -> int:
    """Make a dummy Greg user in the database and return his user ID"""
    uid = new_id()
    await database.set_preferred_name(uid, 'Greg')
    await database.set_pronouns(uid, 'He/Him')
    await database.set_birthday(uid, dt.date(2000, 2, 14))
    await database.set_timezone(uid, pytz.timezone('America/New_York'))
    return uid


@pytest.fixture()
async def invoke_as_greg(message, greg):
    """Create the fake Greg user and set him as the message author"""
    message.author.id = greg


@pytest.fixture()
def apply_new_user_id(new_id, message):
    """Create a new author ID and set it as the message author"""
    id_ = new_id()
    message.author.id = new_id()
    return id_


@pytest.fixture()
def send_in_dms(message):
    """Send the message in DMs (message.guild is None)"""
    # noinspection PyDunderSlots,PyUnresolvedReferences
    message.guild = None


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


@pytest.mark.usefixtures('send_in_dms')
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


@pytest.mark.usefixtures('send_in_dms', 'apply_new_user_id')
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
        embeds = await invoke_cmd_get_embeds(f'name set Greg')
        await self._assert_private(
            embeds, message, database.get_preferred_name, 'Greg', 'name'
        )

    async def test_name_public(self, database, message, invoke_cmd_get_embeds):
        await database.set_privacy_preferred_name(message.author.id, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds(f'name set Greg')
        await self._assert_public(
            embeds, message, database.get_preferred_name, 'Greg'
        )

    async def test_name_too_long_err(self, database, invoke_cmd_get_embeds):
        with pytest.raises(commands.BadArgument, match='64 characters'):
            await invoke_cmd_get_embeds('name set ' + 'a'*65)

    # endregion
    # region Pronouns

    async def test_pronouns_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds(f'pronouns set He/Him')
        await self._assert_private(
            embeds, message, database.get_pronouns, 'He/Him', 'pronouns'
        )

    async def test_pronouns_public(self, database, message, invoke_cmd_get_embeds):
        await database.set_privacy_pronouns(message.author.id, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds(f'pronouns set He/Him')
        await self._assert_public(
            embeds, message, database.get_pronouns, 'He/Him'
        )

    async def test_pronouns_too_long_err(self, database, invoke_cmd_get_embeds):
        with pytest.raises(commands.BadArgument, match='64 characters'):
            await invoke_cmd_get_embeds('pronouns set ' + 'a'*65)

    # endregion
    # region Birthday

    async def test_birthday_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds(f'birthday set 2000-02-14')
        await self._assert_private(
            embeds, message, database.get_birthday, dt.date(2000, 2, 14),
            'birthday'
        )

    async def test_birthday_public(self, database, message, invoke_cmd_get_embeds):
        await database.set_privacy_birthday(message.author.id, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds(f'birthday set 2000-02-14')
        await self._assert_public(
            embeds, message, database.get_birthday, dt.date(2000, 2, 14)
        )

    # endregion
    # region Age

    async def test_age(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds(f'age set 20')
        assert_error(embeds)

    # endregion
    # region Timezone

    async def test_timezone_private(self, database, message, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds(f'timezone set new york')
        await self._assert_private(
            embeds, message, database.get_timezone,
            pytz.timezone('America/New_York'), 'timezone'
        )

    async def test_timezone_public(self, database, message, invoke_cmd_get_embeds):
        await database.set_privacy_timezone(message.author.id, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds(f'timezone set new york')
        await self._assert_public(
            embeds, message, database.get_timezone,
            pytz.timezone('America/New_York')
        )

    # endregion


@pytest.mark.usefixtures('send_in_dms')
class TestDelete:

    @staticmethod
    async def _assert(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod
    ):
        assert len(embeds) == 1
        assert_success(embeds[0])
        value = await db_meth(message.author.id)
        assert value is None

    async def test_name(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('name delete')
        await self._assert(embeds, message, database.get_preferred_name)

    async def test_pronouns(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('pronouns delete')
        await self._assert(embeds, message, database.get_pronouns)

    async def test_birthday(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('birthday delete')
        await self._assert(embeds, message, database.get_birthday)

    async def test_age(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('age delete')
        assert_error(embeds, 'birthday delete')

    async def test_timezone(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('timezone delete')
        await self._assert(embeds, message, database.get_timezone)

    async def test_all(
            self, database, message, invoke_as_greg, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('bio delete')
        assert_success(embeds)
        uid = message.author.id
        assert await database.get_preferred_name(uid) is None
        assert await database.get_pronouns(uid) is None
        assert await database.get_birthday(uid) is None
        assert await database.get_age(uid) is None
        assert await database.get_timezone(uid) is None


class TestWhois:

    @pytest.fixture()
    def user_factory(self, database, new_id, make_user, add_user_to_guild):
        async def f(
                guild: discord.Guild,
                discriminator: int, username: str, display_name: str,
                preferred_name: Optional[str] = None,
                privacy_preferred_name: Optional[PrivacyType] = None,
                pronouns: Optional[str] = None,
                privacy_pronouns: Optional[PrivacyType] = None
        ) -> discord.User:
            user = make_user(new_id(), username, discriminator)
            add_user_to_guild(guild.id, user.id, display_name)

            if preferred_name is not None:
                await database.set_preferred_name(user.id, preferred_name)
            if privacy_preferred_name is not None:
                await database.set_privacy_preferred_name(
                    user.id, privacy_preferred_name
                )

            if pronouns is not None:
                await database.set_pronouns(user.id, pronouns)
            if privacy_pronouns is not None:
                await database.set_privacy_pronouns(user.id, privacy_pronouns)

            return user

        return f

    @pytest.fixture()
    def make_executor(self, user_factory, message):
        async def f(guild: discord.Guild) -> discord.User:
            u = await user_factory(guild, 1000, 'Executor', '_executor_')
            message.author = u
            # noinspection PyDunderSlots,PyUnresolvedReferences
            message.guild = guild
            return u
        return f

    async def test_username(
            self, new_id, make_guild, make_executor, user_factory, message,
            invoke_cmd_get_embeds
    ):
        guild = make_guild(new_id())
        await make_executor(guild)
        other_user = await user_factory(
            guild, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')

    async def test_displayname(
            self, new_id, make_guild, make_executor, user_factory, message,
            invoke_cmd_get_embeds
    ):
        guild = make_guild(new_id())
        await make_executor(guild)
        other_user = await user_factory(
            guild, 1001, 'NoUser', '_Greg_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '_Greg_')

    async def test_preferred_name_private(
            self, new_id, make_guild, make_executor, user_factory, message,
            invoke_cmd_get_embeds
    ):
        guild = make_guild(new_id())
        await make_executor(guild)
        other_user = await user_factory(
            guild, 1001, 'Greg', '_NoDisplay_', '*Greg*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')
        assert '*Greg*' not in embeds[0].description

    async def test_preferred_name_public(
            self, new_id, make_guild, make_executor, user_factory, message,
            invoke_cmd_get_embeds, database
    ):
        guild = make_guild(new_id())
        await make_executor(guild)
        other_user = await user_factory(
            guild, 1001, 'NoUser', '_Greg_', '*NoPreferred*'
        )
        await database.set_privacy_preferred_name(other_user.id, PrivacyType.PUBLIC)
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '_Greg_')

    # noinspection DuplicatedCode
    async def test_main(
            self, new_id, make_guild, add_user_to_guild, user_factory, message,
            invoke_cmd_get_embeds
    ):
        # Should be visible in guild and DMs
        guild0 = make_guild(0)

        u_executor = await user_factory(
            guild0, 1000, 'Executor', '_executor_'
        )
        u_username = await user_factory(
            guild0, 1001, 'Greg', '_blank_', '*Blank*', PrivacyType.PUBLIC
        )
        u_displayname = await user_factory(
            guild0, 1002, 'Blank', '_greg_', '*Blank*', PrivacyType.PUBLIC
        )
        u_preferred_name = await user_factory(
            guild0, 1003, 'Blank', '_blank_', '*Greg*', PrivacyType.PUBLIC
        )
        u_constrained_to_guild = await user_factory(
            guild0, 1004, 'Blank', '_greg_', '*Blank*', PrivacyType.PUBLIC
        )
        u_pronouns = await user_factory(
            guild0, 1005, 'Blank', '_blank_', '*Greg*', PrivacyType.PUBLIC,
            'He/Him', PrivacyType.PUBLIC
        )
        u_no_preferred_name = await user_factory(
            guild0, 1006, 'Greg', '_blank_', None, PrivacyType.PRIVATE,
        )

        # Should only be visible in DMs
        guild1 = make_guild(1)

        add_user_to_guild(guild1.id, u_executor.id, '_executor_'),
        # Test duplicate removal
        add_user_to_guild(guild1.id, u_username.id, '_GregDuplicate_'),
        # Test display names from multiple guilds
        add_user_to_guild(guild1.id, u_constrained_to_guild.id, '_extra_nickname_'),

        u_username1 = await user_factory(
            guild1, 2001, 'GuildHiddenGreg', '_blank_', '*Blank*',
            PrivacyType.PUBLIC
        )
        u_displayname1 = await user_factory(
            guild1, 2002, 'Blank', '_guildhiddengreg_', '*Blank*',
            PrivacyType.PUBLIC
        )
        u_preferred_name1 = await user_factory(
            guild1, 2003, 'Blank', '_blank_', '*GuildHiddenGreg*',
            PrivacyType.PUBLIC
        )

        # Should be totally hidden
        guild2 = make_guild(2)

        u_username2 = await user_factory(
            guild2, 3001, 'TotallyHiddenGreg', '_blank_', '*Blank*',
            PrivacyType.PUBLIC
        )
        u_displayname2 = await user_factory(
            guild2, 3002, 'Blank', '_totallyhiddengreg_', '*Blank*',
            PrivacyType.PUBLIC
        )
        u_preferred_name2 = await user_factory(
            guild2, 3003, 'Blank', '_blank_', '*TotallyHiddenGreg*',
            PrivacyType.PUBLIC
        )

        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = guild0
        message.author = u_executor

        embeds = await invoke_cmd_get_embeds("whois greg")
        assert_info(embeds[0])
        desc: str = embeds[0].description
        assert "*Blank* • Greg#1001 • _blank_" in desc
        assert "*Blank* • Blank#1002 • _greg_" in desc
        assert "*Greg* • Blank#1003 • _blank_" in desc
        assert "*Blank* • Blank#1004 • _greg_" in desc
        assert "*Greg* (He/Him) • Blank#1005 • _blank_" in desc
        assert "`No preferred name` • Greg#1006 • _blank_" in desc

        assert "_extra_nickname_" not in desc
        assert "GuildHiddenGreg#2001" not in desc
        assert "Blank#2002" not in desc
        assert "Blank#2003" not in desc

        assert "TotallyHiddenGreg#3001" not in desc
        assert "Blank#3002" not in desc
        assert "Blank#3003" not in desc

        # Invoke in DMs

        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = None

        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds[0])
        desc: str = embeds[0].description
        assert "*Greg* • Blank#1003 • _blank_" in desc
        assert "*Greg* (He/Him) • Blank#1005 • _blank_" in desc
        assert "*Blank* • Greg#1001 • _blank_" in desc
        assert desc.count('Greg#1001') == 1
        assert "*Blank* • Blank#1002 • _greg_" in desc
        assert "*Blank* • Blank#1004 • _greg_, _extra_nickname_" in desc
        assert "`No preferred name` • Greg#1006 • _blank_" in desc

        assert "*Blank* • GuildHiddenGreg#2001 • _blank_" in desc
        assert "*Blank* • Blank#2002 • _guildhiddengreg_" in desc
        assert "*GuildHiddenGreg* • Blank#2003 • _blank_" in desc

        assert "TotallyHiddenGreg#3001" not in desc
        assert "Blank#3002" not in desc
        assert "Blank#3003" not in desc

        # Erroring commands

        embeds = await invoke_cmd_get_embeds("whois gregothy")
        assert_error(embeds[0], "No users")

        with pytest.raises(commands.BadArgument):
            await invoke_cmd_get_embeds("whois e")
