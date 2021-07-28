import datetime as dt
import logging
from typing import Optional
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytest
import pytz

from .helpers._discord_helpers import *
from .helpers._helpers import patch_all_symbol_imports
from sandpiper.user_data import DatabaseSQLite


# region Discord arrange fixtures


@pytest.fixture()
def new_id():
    last_id = 0
    def f() -> int:
        nonlocal last_id
        last_id += 1
        return last_id
    return f


@pytest.fixture()
def users() -> list[discord.User]:
    return []


@pytest.fixture()
def users_map() -> dict[int, discord.User]:
    return {}


@pytest.fixture()
def make_user(new_id, users, users_map):
    def f(
            id_: Optional[int] = None, name: Optional[str] = None,
            discriminator: Optional[int] = None, **kwargs
    ) -> discord.User:
        """
        Add a mock user to the client. You can access users through the list
        `self.bot.users` or the id->user dict `self.bot.users_map`.

        :param id_: the ID for this user. Must be unique for each test.
        :param name: an optional username for this user
        :param discriminator: an optional discriminator for this user. Defaults
            to the last 4 digits of the ID.
        :param kwargs: extra kwargs to add to the user
        :return: the new User mock
        """

        if id_ is None:
            id_ = new_id()
        if id_ in users_map:
            raise ValueError(f"User with id={id_} already exists")
        if name is None:
            name = 'A_User'
        if discriminator is None:
            discriminator = id_ % 10000

        user = MagicMock_(
            spec=discord.User, id=id_, name=name, discriminator=discriminator,
            **kwargs
        )

        users.append(user)
        users_map[id_] = user
        return user

    return f


@pytest.fixture()
def channels() -> list[discord.TextChannel]:
    return []


@pytest.fixture()
def channels_map() -> dict[int, discord.TextChannel]:
    return {}


@pytest.fixture()
def make_channel(new_id, channels, channels_map):
    def f(
            guild: discord.Guild, id_: Optional[int] = None,
            name: Optional[str] = None, **kwargs
    ) -> discord.TextChannel:
        """
        Add a mock text channel to the client. You can access text channels
        through the id->channel dict `self.bot.channels_map`.

        :param guild: the guild to add this text channel to
        :param id_: the ID for this text channel. Must be unique for each test.
        :param name: an optional name for this text channel
        :param kwargs: extra kwargs to add to the text channel
        :return: the new TextChannel mock
        """

        if id_ is None:
            id_ = new_id()
        if id_ in channels_map:
            raise ValueError(f"Channel with id={id_} already exists")
        if name is None:
            name = 'a-channel'

        channel = MagicMock_(
            spec=discord.TextChannel, id=id_, name=name, **kwargs
        )

        # Add the channel to the guild
        channel.guild = guild
        guild.channels.append(channel)
        guild.text_channels.append(channel)
        # noinspection PyUnresolvedReferences
        guild._channels_map[id_] = channel

        channels.append(channel)
        channels_map[id_] = channel
        return channel

    return f


@pytest.fixture()
def guilds() -> list[discord.Guild]:
    return []


@pytest.fixture()
def guilds_map() -> dict[int, discord.Guild]:
    return {}


@pytest.fixture()
def make_guild(new_id, guilds, guilds_map):
    def f(
            id_: Optional[int] = None, name: Optional[str] = None, **kwargs
    ) -> discord.Guild:
        """
        Add a mock guild to the client. You can access guilds through the list
        `self.bot.guilds` or the id->guild dict `self.bot.guilds_map`.

        :param id_: the ID for this guild. Must be unique for each test.
        :param name: an optional name for this guild
        :param kwargs: extra kwargs to add to the guild
        :return: the new Guild mock
        """

        if id_ is None:
            id_ = new_id()
        if id_ in guilds_map:
            raise ValueError(f"Guild with id={id_} already exists")
        if name is None:
            name = 'A_Guild'

        guild = MagicMock_(spec=discord.Guild, id=id_, name=name, **kwargs)

        guild.members = []
        guild._members_map = members_map = {}
        guild.get_member.side_effect = lambda id: guild._members_map.get(id, None)

        guild.channels = []
        guild._channels_map = channels_map = {}
        guild.get_channel.side_effect = lambda id: guild._channels_map.get(id, None)

        guilds.append(guild)
        guilds_map[id_] = guild
        return guild

    return f


@pytest.fixture()
def add_user_to_guild(users_map, guilds_map):
    def f(
            guild_id: int, user_id: int, display_name: Optional[str], **kwargs
    ) -> discord.Member:
        """
        Create a mock member by adding a user to a guild. The user and guild
        must already exist (created with ``add_user`` or ``add_guild``).

        :param guild_id: the ID of an existing guild to add the user to
        :param user_id: the ID of an existing user to add to the guild
        :param display_name: an optional display name for this member
        :param kwargs: extra kwargs to add to the member
        :return: the new Member mock
        """

        if user_id not in users_map:
            raise ValueError(f"User with id={user_id} does not exist")
        if guild_id not in guilds_map:
            raise ValueError(f"Guild with id={guild_id} does not exist")

        guild = guilds_map[guild_id]
        # noinspection PyUnresolvedReferences
        if user_id in guild._members_map:
            raise ValueError(
                f"Member with id={user_id} already exists in this guild"
            )
        user = users_map[user_id]
        member = MagicMock_(
            spec=discord.Member,
            id=user_id, name=user.name, discriminator=user.discriminator,
            guild=guild, display_name=display_name, **kwargs
        )
        guild.members.append(member)
        # noinspection PyUnresolvedReferences
        guild._members_map[user_id] = member
        return member

    return f


@pytest.fixture()
def message() -> discord.Message:
    # This is the meat of the operation; it allows for message properties
    # to be set where normally it is prohibited
    msg = mock.MagicMock(spec=discord.Message)
    msg.author.bot = False  # Otherwise the invocation will be skipped
    return msg


# noinspection PyPropertyAccess
@pytest.fixture()
async def bot(
        users, users_map, channels, channels_map, guilds, guilds_map
) -> commands.Bot:
    patchers = []

    # Patch in some mocks for bot attributes that tests may need to work
    # with (otherwise they're unsettable)
    for attr in ('users', 'guilds'):
        patcher = mock.patch(f"discord.ext.commands.Bot.{attr}")
        patcher.start()
        patchers.append(patcher)

    # Create a dummy bot that will never actually connect but will help
    # with invocation
    bot = commands.Bot(command_prefix='')

    # I don't need the extreme verbosity of this right now, but for some reason
    # when I set it to False, it shows errors that don't get shown if the
    # method is never called at all...
    bot.loop.set_debug(False)

    # This function checks if message author is the self bot and skips
    # context creation (meaning we won't get command invocation), so
    # we will bypass it
    patcher = mock.patch.object(bot, '_skip_check', return_value=False)
    patcher.start()
    patchers.append(patcher)

    # This connection (discord.state.ConnectionState) object has a `user`
    # field which is accessed by the client's `user` property. The
    # _skip_check function is called with `client.user.id` which doesn't
    # exist (since we aren't connecting) and raises an AttributeError, so
    # we need to patch it in.
    patcher = mock.patch.object(bot, '_connection')
    connection_mock = patcher.start()
    connection_mock.user.id = 0
    patchers.append(patcher)

    patcher = mock.patch.object(bot, 'get_user')
    get_user = patcher.start()
    get_user.side_effect = lambda id: users_map.get(id, None)
    patchers.append(patcher)

    patcher = mock.patch.object(bot, 'get_channel')
    get_channel = patcher.start()
    get_channel.side_effect = lambda id: channels_map.get(id, None)
    patchers.append(patcher)

    patcher = mock.patch.object(bot, 'get_guild')
    get_guild = patcher.start()
    get_guild.side_effect = lambda id: guilds_map.get(id, None)
    patchers.append(patcher)

    bot.guilds = guilds
    bot.users = users

    yield bot

    for patcher in patchers:
        patcher.stop()


# endregion

# region Discord act fixtures


@pytest.fixture()
def invoke_cmd(bot, message):
    async def f(message_content: str) -> mock.AsyncMock:
        """
        Invoke a command with ``self.msg``.

        :param message_content: the message content used to invoke the command
        :return: an AsyncMock representing the `ctx.send` method. You can use
            the methods defined in Mock to check the calls to this method by
            the command invocation.
        """

        message.content = message_content
        ctx = await bot.get_context(message)
        ctx.send = mock.AsyncMock()
        # This is normally done with bot.invoke, but that silently suppresses
        # errors which is BAD!!! >:(
        await ctx.command.invoke(ctx)
        return ctx.send

    return f


@pytest.fixture()
def invoke_cmd_get_embeds(invoke_cmd):
    async def f(message_content: str) -> list[discord.Embed]:
        """
        Invoke a command with ``invoke_cmd`` and return the embeds sent back.

        :param message_content: the message content used to invoke the command
        :return: a list of Embeds sent back after invocation
        """
        send = await invoke_cmd(message_content)
        return get_embeds(send)
    return f


@pytest.fixture()
def dispatch_msg(bot, message):
    async def f(message_content: str) -> mock.AsyncMock:
        """
        Dispatch ``self.msg`` to the client.

        :param message_content: the message content to be dispatched
        :return: an AsyncMock representing the `msg.channel.send` method. You
            can use the methods defined in Mock to check the calls to this
            method by the command invocation.
        """

        message.content = message_content
        message.channel.send = mock.AsyncMock()

        for listener in bot.extra_events.get('on_message', []):
            await listener(message)
        return message.channel.send

    return f


@pytest.fixture()
def dispatch_msg_get_contents(dispatch_msg):
    async def f(message_content: str) -> list[str]:
        """
        Use ``dispatch_msg`` to dispatch ``self.msg`` to the client and
        return the message contents that were sent back.

        :param message_content: the message content to be dispatched
        :return: a list of message contents sent back
        """
        send = await dispatch_msg(message_content)
        return get_contents(send)
    return f


@pytest.fixture()
def dispatch_msg_get_embeds(dispatch_msg):
    async def f(message_content: str) -> list[discord.Embed]:
        """
        Use ``dispatch_msg`` to dispatch ``self.msg`` to the client and
        return a list of embeds that were sent back.

        :param message_content: the message content to be dispatched
        :return: a list of embeds that were sent back
        """
        send = await dispatch_msg(message_content)
        return get_embeds(send)
    return f


# endregion

# region Misc arrange fixtures


@pytest.fixture()
async def database() -> DatabaseSQLite:
    """Create, connect, and patch in a database adapter"""

    # Connect to a dummy database
    db = DatabaseSQLite(':memory:')
    await db.connect()

    # Bypass UserData cog lookup by patching in the database
    patcher = mock.patch(
        'sandpiper.user_data.UserData.get_database', return_value=db
    )
    patcher.start()

    yield db

    await db.disconnect()
    patcher.stop()


@pytest.fixture()
def patch_localzone_utc() -> pytz.UTC:
    # Patch localzone to use UTC
    patcher = mock.patch(
        'tzlocal.get_localzone', autospec=True
    )
    mock_localzone = patcher.start()
    mock_localzone.return_value = pytz.UTC

    yield pytz.UTC

    patcher.stop()


@pytest.fixture()
def patch_datetime() -> list[mock.MagicMock]:
    patchers = patch_all_symbol_imports(dt, 'sandpiper.', 'test')
    dt_mocks = []

    for patcher in patchers:
        mock_datetime = patcher.start()
        dt_mocks.append(mock_datetime)

        mock_datetime.datetime = mock.MagicMock(
            spec=dt.datetime, wraps=dt.datetime)
        mock_datetime.date = mock.MagicMock(spec=dt.date, wraps=dt.date)
        mock_datetime.time = mock.MagicMock(spec=dt.time, wraps=dt.time)
        mock_datetime.timedelta = mock.MagicMock(
            spec=dt.timedelta, wraps=dt.timedelta)

    yield dt_mocks

    for patcher in patchers:
        patcher.stop()


@pytest.fixture()
def patch_datetime_now(patch_datetime):

    def f(static_datetime: dt.datetime) -> dt.datetime:
        for dt_mock in patch_datetime:
            dt_mock.datetime.now.return_value = static_datetime
            dt_mock.date.today.return_value = static_datetime.date()
        return static_datetime

    return f


@pytest.fixture(autouse=True)
def fail_on_log_error(caplog):
    caplog.set_level(logging.ERROR)
    yield

    i = 0
    exc_texts = []
    records = caplog.get_records('setup') + caplog.get_records('call')
    for r in records:
        if not r.levelno == logging.ERROR:
            continue
        if r.exc_text:
            exc_texts.append(f"[Error {i}]\n{r.message}\n{r.exc_text}")
        else:
            exc_texts.append(
                f"[Error {i}]\n{r.message}\n"
                f"(No traceback, but here's the logging location)\n"
                f"  File \"{r.pathname}\", line {r.lineno}"
            )
        i += 1

    if exc_texts:
        exc_texts = '\n\n'.join(exc_texts)
        pytest.fail(
            f"Errors logged during testing:\n{exc_texts}", pytrace=False
        )


# endregion
