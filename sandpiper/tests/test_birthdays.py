import asyncio
import datetime as dt
from typing import Optional
from unittest import mock

import discord
from discord.ext import commands
import pytest
import pytz

from .helpers.discord import *
from .helpers.misc import *
from .helpers.mocking import *
from sandpiper.birthdays import Birthdays
from sandpiper.common.time import TimezoneType
from sandpiper.user_data import PrivacyType, UserData

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def asyncio_sleep():
    return asyncio.sleep


@pytest.fixture()
def birthdays_cog(
        bot, message_templates_with_age, message_templates_no_age
) -> Birthdays:
    cog = Birthdays(
        bot, message_templates_no_age=message_templates_no_age,
        message_templates_with_age=message_templates_with_age
    )
    bot.add_cog(cog)
    cog.daily_loop.count = 1
    cog.daily_loop.cancel()
    return cog


@pytest.fixture()
def bot(bot, database) -> commands.Bot:
    """Add a Bios cog to a bot and return the bot"""
    bot.add_cog(UserData(bot))
    bot.loop.set_debug(True)
    return bot


@pytest.fixture()
def message_templates_no_age() -> list[str]:
    return ["name={name} they={they} ping={ping}"]


@pytest.fixture()
def message_templates_with_age() -> list[str]:
    return ["name={name} they={they} age={age} ping={ping}"]


@pytest.fixture(autouse=True)
def patch_asyncio_sleep(asyncio_sleep):
    async def sleep(time: int, *args, **kwargs):
        if time == 0:
            # This is used to skip the current loop
            await asyncio_sleep(0)
        print(f"Would've slept {time}ms")

    with mock.patch('asyncio.sleep') as mock_sleep:
        mock_sleep.side_effect = sleep
        yield mock_sleep


@pytest.fixture(autouse=True)
def patch_database_isinstance():
    with mock.patch(
        'sandpiper.user_data.database_sqlite.isinstance',
        wraps=isinstance_mock_supported
    ):
        yield


@pytest.fixture(autouse=True)
def patch_time(
        patch_datetime_now, patch_localzone_utc, patch_database_isinstance
) -> dt.datetime:
    return patch_datetime_now(dt.datetime(2020, 2, 14, 0, 0))


@pytest.fixture()
def run_daily_loop_once(birthdays_cog):
    async def f():
        birthdays_cog.daily_loop.start()
        # Wait for the birthday scheduling task to finish
        await birthdays_cog.daily_loop.get_task()
        # Wait for the birthday sending task to finish
        await asyncio.gather(*birthdays_cog.tasks.values())
    return f


@pytest.fixture()
def user_factory(add_user_to_guild, database, make_user, new_id):
    async def f(
            *,
            guild: Optional[discord.Guild] = None,
            display_name: Optional[str] = None,
            name: Optional[str] = None,
            pronouns: Optional[str] = None,
            birthday: Optional[dt.date] = None,
            timezone: Optional[TimezoneType] = None,
            p_name: PrivacyType = PrivacyType.PUBLIC,
            p_pronouns: PrivacyType = PrivacyType.PUBLIC,
            p_birthday: PrivacyType = PrivacyType.PUBLIC,
            p_age: PrivacyType = PrivacyType.PUBLIC,
            p_timezone: PrivacyType = PrivacyType.PUBLIC,
    ) -> int:
        uid = new_id()

        make_user(uid)
        if guild is not None:
            add_user_to_guild(guild.id, uid, display_name)

        await database.create_user(uid)
        await database.set_preferred_name(uid, name)
        await database.set_pronouns(uid, pronouns)
        await database.set_birthday(uid, birthday)
        await database.set_timezone(uid, timezone)
        await database.set_privacy_preferred_name(uid, p_name)
        await database.set_privacy_pronouns(uid, p_pronouns)
        await database.set_privacy_birthday(uid, p_birthday)
        await database.set_privacy_age(uid, p_age)
        await database.set_privacy_timezone(uid, p_timezone)

        return uid

    return f


class TestBirthdays:

    async def test_basic(
            self, make_channel, make_guild, patch_asyncio_sleep,
            run_daily_loop_once, user_factory
    ):
        guild = make_guild()
        chan = make_channel(guild)
        uid = await user_factory(
            guild=guild, birthday=dt.date(2000, 2, 14),
            timezone=pytz.timezone('UTC')
        )
        await run_daily_loop_once()
        pass

