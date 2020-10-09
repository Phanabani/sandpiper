import logging
from textwrap import wrap
from typing import Any, Dict, Optional, Tuple, Type, Union, cast

import discord
import discord.ext.commands as commands

from .database import Database, DatabaseError
from .enums import PrivacyType

__all__ = ['UserData']

logger = logging.getLogger('sandpiper.user_info')


class DatabaseUnavailable(commands.CheckFailure):
    pass


class UserFeedbackError(Exception):
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


class Embeds:

    INFO_COLOR = 0x5E5FFF
    SUCCESS_COLOR = 0x57FCA5
    ERROR_COLOR = 0xFF0000

    @classmethod
    def fields(cls, *fields: Tuple[str, Optional[Any], int]) -> discord.Embed:
        """
        Creates a Discord embed to display user info.

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
            value_wrapped = wrap(value, width=50, subsequent_indent='  ')
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
        return embed

    @classmethod
    def info(cls, message: str):
        return discord.Embed(title='Info', description=message,
                             color=cls.INFO_COLOR)

    @classmethod
    def success(cls, message: str):
        return discord.Embed(title='Success', description=message,
                             color=cls.SUCCESS_COLOR)

    @classmethod
    def error(cls, reason: Union[Type[Exception], Exception, str]):
        if isinstance(reason, (type, Exception)):
            reason = ErrorMessages.get(reason)
        return discord.Embed(title='Error', description=reason,
                             color=cls.ERROR_COLOR)


def is_database_available():
    async def predicate(ctx: commands.Context):
        # noinspection PyProtectedMember
        db_connected = cast(UserData, ctx.cog).database.connected()
        if not db_connected:
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
            await ctx.send(embed=Embeds.error(error.original))
        else:
            await ctx.send(embed=Embeds.error(error))

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
        embed = Embeds.fields(
            ('Name', preferred_name, privacy_preferred_name),
            ('Pronouns', pronouns, privacy_pronouns),
            ('Birthday', birthday, privacy_birthday),
            ('Age', age, privacy_age),
            ('Timezone', timezone, privacy_timezone),
        )
        await ctx.send(embed=embed)

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
        embed = Embeds.fields(('Name', preferred_name, privacy))
        await ctx.send(embed=embed)

    @bio_set.command(name='name')
    @is_database_available()
    @commands.dm_only()
    async def bio_set_name(self, ctx: commands.Context, new_name: str):
        """Set your preferred name."""
        user_id: int = ctx.author.id
        try:
            self.database.set_preferred_name(user_id, new_name)
        except DatabaseError:
            await ctx.send(embed=Embeds.error(DatabaseError))

    @commands.command(name='who is')
    @is_database_available()
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
