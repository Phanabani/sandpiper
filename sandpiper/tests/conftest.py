from typing import Optional
import unittest.mock as mock

import discord
import discord.ext.commands as commands
import pytest


# noinspection PyPep8Naming
class MagicMock_(mock.MagicMock):
    """
    Identical to MagicMock, but the ``name`` kwarg will be parsed as a regular
    kwarg (assigned to the mock as an attribute).
    """

    def __init__(self, *args, _name_: Optional[str] = None, **kwargs):
        if _name_ is None:
            _name_ = ''
        name_attr = kwargs.pop('name', None)
        super().__init__(*args, name=_name_, **kwargs)
        self.name = name_attr


@pytest.fixture()
def users() -> list[discord.User]:
    return []


@pytest.fixture()
def users_map() -> dict[int, discord.User]:
    return {}


@pytest.fixture()
def make_user(users, users_map):
    def f(
            id_: int, name: Optional[str] = None,
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
def guilds() -> list[discord.Guild]:
    return []


@pytest.fixture()
def guilds_map() -> dict[int, discord.Guild]:
    return {}


@pytest.fixture()
def make_guild(guilds, guilds_map):
    def f(id_: int, name: Optional[str] = None, **kwargs) -> discord.Guild:
        """
        Add a mock guild to the client. You can access guilds through the list
        `self.bot.guilds` or the id->guild dict `self.bot.guilds_map`.

        :param id_: the ID for this guild. Must be unique for each test.
        :param name: an optional username for this guild
        :param kwargs: extra kwargs to add to the guild
        :return: the new Guild mock
        """

        if id_ in guilds_map:
            raise ValueError(f"Guild with id={id_} already exists")
        if name is None:
            name = 'A_Guild'

        guild = MagicMock_(spec=discord.Guild, id=id_, name=name, **kwargs)
        members = []
        members_map = {}
        guild.members = members
        guild._members_map = members_map
        guild.get_member.side_effect = lambda id: members_map.get(id, None)
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
            raise ValueError(f"Member with id={user_id} already exists in "
                             f"this guild")
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
def message():
    # This is the meat of the operation; it allows for message properties
    # to be set where normally it is prohibited
    msg = mock.MagicMock(spec=discord.Message)
    msg.author.bot = False  # Otherwise the invocation will be skipped
    return msg


# noinspection PyPropertyAccess
@pytest.fixture()
async def bot(users, users_map, guilds, guilds_map):
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

    patcher = mock.patch.object(bot, 'get_guild')
    get_guild = patcher.start()
    get_guild.side_effect = lambda id: guilds_map.get(id, None)
    patchers.append(patcher)

    bot.guilds = guilds
    bot.users = users

    yield bot

    for patcher in patchers:
        patcher.stop()
