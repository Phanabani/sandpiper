from typing import *
import unittest
import unittest.mock as mock

import discord
import discord.ext.commands as commands

__all__ = ['DiscordMockingTestCase', 'MagicMock_']


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


class DiscordMockingTestCase(unittest.IsolatedAsyncioTestCase):

    _next_user_id: int
    msg: mock.MagicMock

    def setUp(self):
        self._next_user_id = 1

    async def asyncSetUp(self):
        # This is the meat of the operation; it allows for message properties
        # to be set where normally it is prohibited
        self.msg = mock.MagicMock(spec=discord.Message)
        self.msg.author.bot = False  # Otherwise the invocation will be skipped

        # Patch in some mocks for bot attributes that tests may need to work
        # with (otherwise they're unsettable)
        for attr in ('users', 'guilds'):
            patcher = mock.patch(f"discord.ext.commands.Bot.{attr}")
            patcher.start()
            self.addCleanup(patcher.stop)

        # Create a dummy bot that will never actually connect but will help
        # with invocation
        self.bot = commands.Bot(command_prefix='')
        self.add_cogs(self.bot)

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

        self.init_mock_userdata()

    def add_cogs(self, bot: commands.Bot):
        """Override to add cogs to the bot!"""
        pass

    # noinspection PyPropertyAccess
    def init_mock_userdata(self):
        self.guilds: List[mock.Mock] = []
        self.users: List[mock.Mock] = []
        self.guilds_map: Dict[int, mock.Mock] = {}
        self.users_map: Dict[int, mock.Mock] = {}

        patcher = mock.patch.object(self.bot, 'get_user')
        get_user = patcher.start()
        get_user.side_effect = lambda id: self.users_map.get(id, None)
        self.addCleanup(patcher.stop)

        # These are patched in in asyncSetUp
        self.bot.guilds = self.guilds
        self.bot.users = self.users

    # region Mock Discord data

    def add_user(
            self, id: int, name: Optional[str] = None,
            discriminator: Optional[int] = None, **kwargs
    ) -> discord.User:
        """
        Add a mock user to the client. You can access users through the list
        `self.bot.users` or the id->user dict `self.bot.users_map`.

        :param id: the ID for this user. Must be unique for each test.
        :param name: an optional username for this user
        :param discriminator: an optional discriminator for this user. Defaults
            to the last 4 digits of the ID.
        :param kwargs: extra kwargs to add to the user
        :return: the new User mock
        """

        if id in self.users_map:
            raise ValueError(f"User with id={id} already exists")
        if name is None:
            name = 'A_User'
        if discriminator is None:
            discriminator = id % 10000
        user = MagicMock_(spec=discord.User, id=id, name=name,
                          discriminator=discriminator, **kwargs)
        self.users.append(user)
        self.users_map[id] = user
        return user

    def add_guild(self, id: int, name: Optional[str] = None,
                  **kwargs) -> discord.Guild:
        """
        Add a mock guild to the client. You can access guilds through the list
        `self.bot.guilds` or the id->guild dict `self.bot.guilds_map`.

        :param id: the ID for this guild. Must be unique for each test.
        :param name: an optional username for this guild
        :param kwargs: extra kwargs to add to the guild
        :return: the new Guild mock
        """

        if id in self.guilds_map:
            raise ValueError(f"Guild with id={id} already exists")
        if name is None:
            name = 'A_Guild'

        guild = MagicMock_(spec=discord.Guild, id=id, name=name, **kwargs)
        members = []
        members_map = {}
        guild.members = members
        guild._members_map = members_map
        guild.get_member.side_effect = lambda id: members_map.get(id, None)
        self.guilds.append(guild)
        self.guilds_map[id] = guild
        return guild

    def add_user_to_guild(self, guild_id: int, user_id: int,
                          display_name: Optional[str],
                          **kwargs) -> discord.Member:
        """
        Create a mock member by adding a user to a guild. The user and guild
        must already exist (created with ``add_user`` or ``add_guild``).

        :param guild_id: the ID of an existing guild to add the user to
        :param user_id: the ID of an existing user to add to the guild
        :param display_name: an optional display name for this member
        :param kwargs: extra kwargs to add to the member
        :return: the new Member mock
        """

        if user_id not in self.users_map:
            raise ValueError(f"User with id={user_id} does not exist")
        if guild_id not in self.guilds_map:
            raise ValueError(f"Guild with id={guild_id} does not exist")

        guild = self.guilds_map[guild_id]
        if user_id in guild._members_map:
            raise ValueError(f"Member with id={user_id} already exists in "
                             f"this guild")
        user = self.users_map[user_id]
        member = MagicMock_(
            spec=discord.Member,
            id=user_id, name=user.name, discriminator=user.discriminator,
            guild=guild, display_name=display_name, **kwargs
        )
        guild.members.append(member)
        guild._members_map[user_id] = member
        return member

    # endregion

    # region Message dispatching and command invocation

    @staticmethod
    def get_embeds(mock_: MagicMock_) -> List[discord.Embed]:
        """
        :param mock_: a mock ``send`` method
        :return: a list of embeds sent in each message
        """
        return [
            embed for call in mock_.call_args_list
            if (embed := call.kwargs.get('embed'))
        ]

    @staticmethod
    def get_contents(mock_: MagicMock_) -> List[str]:
        """
        :param mock_: a mock ``send`` method
        :return: a list of each message's contents
        """
        return [
            content for call in mock_.call_args_list
            if (content := call.args[0]) is not None
        ]

    async def invoke_cmd(self, message_content: str) -> mock.AsyncMock:
        """
        Invoke a command with ``self.msg``.

        :param message_content: the message content used to invoke the command
        :return: an AsyncMock representing the `ctx.send` method. You can use
            the methods defined in Mock to check the calls to this method by
            the command invocation.
        """

        self.msg.content = message_content
        ctx = await self.bot.get_context(self.msg)
        ctx.send = mock.AsyncMock()
        # This is normally done with bot.invoke, but that silently suppresses
        # errors which is BAD!!! >:(
        await ctx.command.invoke(ctx)
        return ctx.send

    async def invoke_cmd_get_embeds(
            self, message_content: str
    ) -> List[discord.Embed]:
        """
        Invoke a command with ``invoke_cmd`` and return the embeds sent back.

        :param message_content: the message content used to invoke the command
        :return: a list of Embeds sent back after invocation
        """

        send = await self.invoke_cmd(message_content)
        return self.get_embeds(send)

    async def dispatch_msg(self, message_content: str) -> mock.AsyncMock:
        """
        Dispatch ``self.msg`` to the client.

        :param message_content: the message content to be dispatched
        :return: an AsyncMock representing the `msg.channel.send` method. You
            can use the methods defined in Mock to check the calls to this
            method by the command invocation.
        """

        self.msg.content = message_content
        self.msg.channel.send = mock.AsyncMock()

        for listener in self.bot.extra_events.get('on_message', []):
            await listener(self.msg)
        return self.msg.channel.send

    @overload
    async def dispatch_msg_get_contents(
            self, message_content: str
    ) -> List[str]:
        pass

    @overload
    async def dispatch_msg_get_contents(
            self, message_content: str, only_one: Literal[False]
    ) -> List[str]:
        pass

    @overload
    async def dispatch_msg_get_contents(
            self, message_content: str, only_one: Literal[True]
    ) -> str:
        pass

    async def dispatch_msg_get_contents(
            self, message_content: str, only_one = False
    ) -> Union[List[str], str]:
        """
        Use ``dispatch_msg`` to dispatch ``self.msg`` to the client and
        return the message contents that were sent back.

        :param message_content: the message content to be dispatched
        :return: one or more message contents sent back
        """

        send = await self.dispatch_msg(message_content)
        contents = self.get_contents(send)
        if only_one:
            self.assertEqual(
                len(contents), 1, msg=f"Expected 1 message, got {len(contents)}"
            )
            return contents[0]
        return contents

    @overload
    async def dispatch_msg_get_embeds(
            self, message_content: str
    ) -> List[discord.Embed]:
        pass

    @overload
    async def dispatch_msg_get_embeds(
            self, message_content: str, only_one: Literal[False] = False
    ) -> List[discord.Embed]:
        pass

    @overload
    async def dispatch_msg_get_embeds(
            self, message_content: str, only_one: Literal[True] = False
    ) -> discord.Embed:
        pass

    async def dispatch_msg_get_embeds(
            self, message_content: str, only_one = False
    ) -> Union[List[discord.Embed], discord.Embed]:
        """
        Use ``dispatch_msg`` to dispatch ``self.msg`` to the client and
        return a list of embeds that were sent back.

        :param message_content: the message content to be dispatched
        :param only_one: assert the number of embeds is 1 and return it
        :return: one or more embeds that were sent back
        """

        send = await self.dispatch_msg(message_content)
        embeds = self.get_embeds(send)
        if only_one:
            self.assertEqual(
                len(embeds), 1, msg=f"Expected 1 embed, got {len(embeds)}"
            )
            return embeds[0]
        return embeds

    # endregion

    # region Embed assertions

    def assert_success(self, embed: discord.Embed, *substrings: str):
        """
        Assert ``embed`` is a success embed and that its description contains
        each substring in ``substrings``.
        """
        self.assertIn('Success', embed.title)
        for substr in substrings:
            self.assertIn(substr, embed.description)

    def assert_warning(self, embed: discord.Embed, *substrings: str):
        """
        Assert ``embed`` is a warning embed and that its description contains
        each substring in ``substrings``.
        """
        self.assertIn('Warning', embed.title)
        for substr in substrings:
            self.assertIn(substr, embed.description)

    def assert_error(self, embed: discord.Embed, *substrings: str):
        """
        Assert ``embed`` is an error embed and that its description contains
        each substring in ``substrings``.
        """
        self.assertIn('Error', embed.title)
        for substr in substrings:
            self.assertIn(substr, embed.description)

    def assert_info(self, embed: discord.Embed, *substrings: str):
        """
        Assert ``embed`` is an info embed and that its description contains
        each substring in ``substrings``.
        """
        self.assertIn('Info', embed.title)
        for substr in substrings:
            self.assertIn(substr, embed.description)

    # endregion

    # region Content assertions

    async def assert_in_reply(self, msg: str, *substrings: str) -> NoReturn:
        """
        Dispatch ``msg`` to the bot and assert that it replies with one
        message and contains each substring in ``substrings``.
        """
        msg = await self.dispatch_msg_get_contents(msg, only_one=True)
        for substr in substrings:
            self.assertIn(substr, msg)

    async def assert_regex_reply(self, msg: str, *patterns: str) -> NoReturn:
        """
        Dispatch ``msg`` to the bot and assert that it replies with one
        message and matches each regex pattern in ``patterns``.
        """
        msg = await self.dispatch_msg_get_contents(msg, only_one=True)
        for pattern in patterns:
            self.assertRegex(msg, pattern)

    # endregion

    def new_user_id(self) -> int:
        """
        Get a new, unique user ID (increments by one each call).
        """
        uid = self._next_user_id
        self._next_user_id += 1
        return uid
