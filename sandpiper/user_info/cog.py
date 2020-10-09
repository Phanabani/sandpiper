import logging
from textwrap import wrap
from typing import Any, Dict, Optional, Tuple, Type, Union

import discord
import discord.ext.commands as commands

from ..common.embeds import Embeds as EmbedsBase
from ..common.errors import UserFeedbackError
from .database import Database, DatabaseError
from .enums import PrivacyType

__all__ = ['UserData']

logger = logging.getLogger('sandpiper.user_info')


class DatabaseUnavailable(commands.CheckFailure):
    pass


class ErrorMessages:

    default_msg = 'Unexpected error.'
    error_msgs: Dict[Type[Exception], str] = {
        commands.PrivateMessageOnly:
            'For your privacy, DM me to use this command.',
        DatabaseUnavailable:
            'Unable to access database.',
        DatabaseError:
            'Error during database operation.',
    }

    @classmethod
    def get(cls, error: Union[Type[Exception], Exception] = None):
        if isinstance(error, UserFeedbackError):
            return str(error)

        if isinstance(error, Exception):
            error = type(error)
        if error in cls.error_msgs:
            return cls.error_msgs[error]

        logger.error(f'Unexpected error {error}', exc_info=True)
        return cls.default_msg


class Embeds(EmbedsBase):

    @classmethod
    async def user_info(cls, messageable: discord.abc.Messageable,
                        *fields: Tuple[str, Optional[Any], int]):
        """
        Sends a Discord embed displaying user info.

        :param messageable: Where to send message
        :param fields: Tuples of (col_name, value, privacy)
        :returns: An embed with tabulated user info
        """

        field_names = []
        values = []
        privacies = []
        for field_name, value, privacy in fields:
            if value is None:
                value = '*Not set*'
            else:
                value = str(value)
            privacy = PrivacyType(privacy).name.capitalize()

            # Wrap the value in case it's long
            value_wrapped = wrap(value, width=40, subsequent_indent='  ')
            # Used to add blank lines to the other fields (so they stay lined up
            # with wrapped values)
            wrap_padding = [''] * (len(value_wrapped) - 1)

            field_names.extend([field_name] + wrap_padding)
            values.extend(value_wrapped)
            privacies.extend([privacy] + wrap_padding)

        embed = discord.Embed(title=f'Your info', color=cls.INFO_COLOR)
        embed.add_field(name='Field', value='\n'.join(field_names), inline=True)
        embed.add_field(name='Value', value='\n'.join(values), inline=True)
        embed.add_field(name='Privacy', value='\n'.join(privacies), inline=True)
        await messageable.send(embed=embed)


def is_database_available():
    async def predicate(ctx: commands.Context):
        # noinspection PyProtectedMember
        cog: Optional[UserData] = ctx.cog
        if cog is None:
            logger.error(f'Command has no associated cog ('
                         f'content={ctx.message.content} '
                         f'msg={ctx.message} '
                         f'command={ctx.command})')
            raise commands.CheckFailure('Unexpected error.')
        elif not cog.database.connected():
            raise DatabaseUnavailable()
        return True
    return commands.check(predicate)


class UserData(commands.Cog):

    database: Database = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def set_database_adapter(self, database: Database):
        self.database = database

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context,
                               error: commands.CommandError):
        if isinstance(error, commands.CommandInvokeError):
            reason = ErrorMessages.get(error.original)
        else:
            reason = ErrorMessages.get(error)
        await Embeds.error(ctx, reason)

    @commands.group()
    async def bio(self, ctx: commands.Context):
        """Commands for managing your personal info."""
        pass

    @bio.command(name='clear')
    @is_database_available()
    @commands.dm_only()
    async def bio_clear(self, ctx: commands.Context):
        """Deletes all of your personal info."""
        user_id: int = ctx.author.id
        self.database.clear_data(user_id)

    @bio.group(name='show', invoke_without_command=True)
    @is_database_available()
    @commands.dm_only()
    async def bio_show(self, ctx: commands.Context):
        """
        Commands for displaying your personal info. Can be run on its own to
        display all stored info.
        """

        user_id: int = ctx.author.id
        preferred_name = self.database.get_preferred_name(user_id)
        privacy_preferred_name = self.database.get_privacy_preferred_name(user_id)
        pronouns = self.database.get_pronouns(user_id)
        privacy_pronouns = self.database.get_privacy_pronouns(user_id)
        birthday = self.database.get_birthday(user_id)
        privacy_birthday = self.database.get_privacy_birthday(user_id)
        age = self.database.get_age(user_id)
        privacy_age = self.database.get_privacy_age(user_id)
        timezone = self.database.get_timezone(user_id)
        privacy_timezone = self.database.get_privacy_timezone(user_id)
        await Embeds.user_info(
            ctx,
            ('Name', preferred_name, privacy_preferred_name),
            ('Pronouns', pronouns, privacy_pronouns),
            ('Birthday', birthday, privacy_birthday),
            ('Age', age, privacy_age),
            ('Timezone', timezone, privacy_timezone),
        )

    @bio.group(name='set', invoke_without_command=False)
    async def bio_set(self, ctx: commands.Context):
        """Commands for setting your personal info."""
        pass

    # Name

    @bio_show.command(name='name')
    @is_database_available()
    @commands.dm_only()
    async def bio_show_name(self, ctx: commands.Context):
        """Display your preferred name."""
        user_id: int = ctx.author.id
        preferred_name = self.database.get_preferred_name(user_id)
        privacy = self.database.get_privacy_preferred_name(user_id)
        await Embeds.user_info(ctx, ('Name', preferred_name, privacy))

    @bio_set.command(name='name')
    @is_database_available()
    @commands.dm_only()
    async def bio_set_name(self, ctx: commands.Context, new_name: str):
        """Set your preferred name."""
        user_id: int = ctx.author.id
        if len(new_name) > 64:
            raise UserFeedbackError(f'Name must be 64 characters or less ('
                                    f'yours: {len(new_name)}).')
        self.database.set_preferred_name(user_id, new_name)
        await Embeds.success(ctx, 'Name set!')

    # Other

    @commands.command(name='who is')
    @is_database_available()
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
