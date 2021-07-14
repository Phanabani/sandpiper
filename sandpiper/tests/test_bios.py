from collections.abc import Awaitable, Callable
import datetime as dt
from typing import Optional

import discord
import discord.ext.commands as commands
import pytest
import pytz

from ._helpers import *
from ._discord_helpers import *
from sandpiper.bios import Bios
from sandpiper.user_data import DatabaseSQLite, UserData
from sandpiper.user_data.enums import PrivacyType

pytestmark = pytest.mark.asyncio

T_DatabaseMethod = Callable[[int], Awaitable[PrivacyType]]


@pytest.fixture()
def bot(bot) -> commands.Bot:
    """Add a Bios cog to a bot and return the bot"""
    bot.add_cog(Bios(bot))
    bot.add_cog(UserData(bot))
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


@pytest.fixture()
def send_in_guild(new_id, make_guild, message):
    """Send the message in DMs (message.guild is None)"""
    guild = make_guild(new_id())
    # noinspection PyDunderSlots,PyUnresolvedReferences
    message.guild = guild


@pytest.mark.usefixtures('apply_new_user_id')
class TestPrivacy:

    @staticmethod
    async def _assert(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod, privacy: PrivacyType
    ):
        """
        Use the database method ``db_meth`` to assert the command successfully
        changed the privacy field.
        """
        __tracebackhide__ = True
        assert_success(embeds)
        assert await db_meth(message.author.id) is privacy

    @staticmethod
    async def _assert_all(
            embeds: list[discord.Embed], message: discord.Message,
            db: DatabaseSQLite, privacy: PrivacyType
    ):
        """
        Assert that every database field is ``privacy``.
        """
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

    @pytest.fixture()
    def june_1st_2020_932_am(
            self, patch_localzone_utc, patch_datetime_now
    ) -> dt.datetime:
        yield patch_datetime_now(dt.datetime(2020, 6, 1, 9, 32))

    async def test_name(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('name show')
        assert_info(embeds, 'Greg')

    async def test_pronouns(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('pronouns show')
        assert_info(embeds, 'He/Him')

    async def test_birthday(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('birthday show')
        assert_info(embeds, '2000-02-14')

    async def test_age(
            self, invoke_as_greg, invoke_cmd_get_embeds,
            june_1st_2020_932_am
    ):
        embeds = await invoke_cmd_get_embeds('age show')
        assert_info(embeds)
        assert_regex(embeds[0].description, 'Age.+20')

    async def test_timezone(self, invoke_as_greg, invoke_cmd_get_embeds):
        embeds = await invoke_cmd_get_embeds('timezone show')
        assert_info(embeds, 'America/New_York')

    async def test_all(
            self, invoke_as_greg, invoke_cmd_get_embeds,
            june_1st_2020_932_am
    ):
        embeds = await invoke_cmd_get_embeds('bio show')
        assert_info(embeds)
        assert_regex(
            embeds[0].description,
            'Name.+Greg', 'Pronouns.+He/Him', 'Birthday.+2000-02-14',
            'Age.+20', 'Timezone.+America/New_York'
        )


@pytest.mark.usefixtures('send_in_dms', 'apply_new_user_id')
class TestSet:

    @staticmethod
    async def _assert_private(
            embeds: list[discord.Embed], message: discord.Message,
            db_meth: T_DatabaseMethod, expected_value, privacy_field_name: str
    ):
        """
        Assert the set succeeded and that a warning message is also sent
        telling the user how they can make this field public if they want.
        """
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
        """
        Assert that the test succeeded.
        """
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
        """
        Use the database method ``db_meth`` to assert the command successfully
        deleted the data.
        """
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
    def main_guild(self, new_id, make_guild) -> discord.Guild:
        return make_guild(new_id())

    @pytest.fixture()
    def secondary_guild(self, new_id, make_guild) -> discord.Guild:
        return make_guild(new_id())

    @pytest.fixture()
    def user_factory(
            self, database, new_id, make_user, add_user_to_guild, main_guild
    ):
        async def f(
                guild: Optional[discord.Guild],
                discriminator: int, username: str, display_name: str,
                preferred_name: Optional[str] = None,
                privacy_preferred_name: Optional[PrivacyType] = None,
                pronouns: Optional[str] = None,
                privacy_pronouns: Optional[PrivacyType] = None
        ) -> discord.User:

            if guild is None:
                guild = main_guild

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
    async def executor(self, main_guild, user_factory, message) -> discord.User:
        u = await user_factory(None, 1000, 'Executor', '_executor_')
        message.author = u
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = main_guild
        return u

    @pytest.fixture()
    async def multiple_display_names_user(
            self, executor, user_factory, new_id, make_guild,
            add_user_to_guild, secondary_guild
    ) -> discord.User:
        other_user = await user_factory(
            None, 1001, 'Greg', '_Greg1_', '*NoPreferred*',
            PrivacyType.PUBLIC
        )
        add_user_to_guild(secondary_guild.id, other_user.id, '_Greg2_')
        return other_user

    @pytest.fixture()
    async def executor_in_secondary_guild(
            self, executor, secondary_guild, add_user_to_guild
    ):
        # noinspection PyUnresolvedReferences
        add_user_to_guild(secondary_guild.id, executor.id, '_NoDisplay_')

    # region Same guild

    async def test_username(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')

    async def test_username_with_discriminator(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*'
        )
        other_user = await user_factory(
            None, 1002, 'Greg', '_NoDisplay_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg#1002')
        assert_info(embeds)
        assert 'Greg#1001' not in embeds[0].description
        assert 'Greg#1002' in embeds[0].description

    async def test_display_name(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'NoUser', '_Greg_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '_Greg_')

    async def test_preferred_name_private(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'Greg', '_NoDisplay_', '*Greg*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')
        assert '*Greg*' not in embeds[0].description

    async def test_preferred_name_public(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'NoUser', '_Greg_', '*NoPreferred*',
            PrivacyType.PUBLIC
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '_Greg_')

    async def test_pronouns_private(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*',
            None, 'He/Him', privacy_pronouns=PrivacyType.PRIVATE
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')
        assert 'He/Him' not in embeds[0].description

    async def test_pronouns_public(
            self, executor, user_factory, message, invoke_cmd_get_embeds
    ):
        other_user = await user_factory(
            None, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*',
            None, 'He/Him', privacy_pronouns=PrivacyType.PUBLIC
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg#1001')
        assert 'He/Him' in embeds[0].description

    # endregion
    # region Don't show stuff from different guilds

    async def test_username_different_guild(
            self, executor, user_factory, message, invoke_cmd_get_embeds,
            new_id, make_guild, add_user_to_guild
    ):
        other_guild = make_guild(new_id())
        other_user = await user_factory(
            other_guild, 1001, 'Greg', '_NoDisplay_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_error(embeds, 'No user')

        # Sanity check that this user can actually be found
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = other_guild
        # noinspection PyUnresolvedReferences
        add_user_to_guild(other_guild.id, executor.id, '_NoDisplay_')
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, 'Greg')

    async def test_display_name_different_guild(
            self, executor, user_factory, message, invoke_cmd_get_embeds,
            new_id, make_guild, add_user_to_guild
    ):
        other_guild = make_guild(new_id())
        other_user = await user_factory(
            other_guild, 1001, 'NoUser', '_Greg_', '*NoPreferred*'
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_error(embeds, 'No user')

        # Sanity check that this user can actually be found
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = other_guild
        # noinspection PyUnresolvedReferences
        add_user_to_guild(other_guild.id, executor.id, '_NoDisplay_')
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '_Greg_')

    async def test_preferred_name_different_guild(
            self, executor, user_factory, message, invoke_cmd_get_embeds,
            new_id, make_guild, add_user_to_guild
    ):
        other_guild = make_guild(new_id())
        other_user = await user_factory(
            other_guild, 1001, 'NoUser', '_NoDisplay_', '*Greg*',
            PrivacyType.PUBLIC
        )
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_error(embeds, 'No user')

        # Sanity check that this user can actually be found
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = other_guild
        # noinspection PyUnresolvedReferences
        add_user_to_guild(other_guild.id, executor.id, '_NoDisplay_')
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds, '*Greg*')

    # endregion
    # region Multiple display names

    async def test_multiple_display_names_in_main_guild(
            self, executor, message, invoke_cmd_get_embeds,
            multiple_display_names_user, executor_in_secondary_guild
    ):
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds)
        assert '_Greg1_' in embeds[0].description
        assert '_Greg2_' not in embeds[0].description

    async def test_multiple_display_names_in_dms(
            self, executor, message, invoke_cmd_get_embeds,
            multiple_display_names_user, executor_in_secondary_guild
    ):
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = None
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds)
        assert '_Greg1_' in embeds[0].description
        assert '_Greg2_' in embeds[0].description

    async def test_multiple_display_names_in_dms_only_main_guild(
            self, executor, message, invoke_cmd_get_embeds,
            multiple_display_names_user
    ):
        # noinspection PyDunderSlots,PyUnresolvedReferences
        message.guild = None
        embeds = await invoke_cmd_get_embeds('whois greg')
        assert_info(embeds)
        assert '_Greg1_' in embeds[0].description
        assert '_Greg2_' not in embeds[0].description

    # endregion
    # region Invalid things

    async def test_no_user_found(
            self, executor, invoke_cmd_get_embeds
    ):
        embeds = await invoke_cmd_get_embeds('whois gregothy')
        assert_error(embeds)

    async def test_below_minimum_characters(
            self, executor, invoke_cmd_get_embeds
    ):
        with pytest.raises(commands.BadArgument):
            await invoke_cmd_get_embeds("whois e")

    # endregion


@pytest.mark.usefixtures('apply_new_user_id')
class TestAllowPublicBioSetting:

    @pytest.fixture(autouse=True)
    async def set_privacies_public(self, apply_new_user_id, database, message):
        await database.set_privacy_preferred_name(
            message.author.id, PrivacyType.PUBLIC
        )

    @pytest.fixture()
    def allow_public_bio_setting(self, bot):
        bios: Bios = bot.get_cog('Bios')
        bios.allow_public_setting = True

    async def test_disallow_set(
            self, database, message, invoke_cmd_get_embeds, send_in_guild
    ):
        with pytest.raises(commands.PrivateMessageOnly):
            await invoke_cmd_get_embeds(f'name set Greg')

    async def test_allow_set(
            self, database, message, invoke_cmd_get_embeds, send_in_guild,
            allow_public_bio_setting
    ):
        embeds = await invoke_cmd_get_embeds(f'name set Greg')
        assert_success(embeds)
