import logging
from textwrap import wrap
from typing import Any, Dict, Optional, Tuple, Type, cast

import discord
import discord.ext.commands as commands

from .database import Database
from .enums import PrivacyType

__all__ = ['UserData']

logger = logging.getLogger('sandpiper.user_info')
EMBED_COLOR = 0x5E5FFF


def make_embed(*fields: Tuple[str, Optional[Any], int]) -> discord.Embed:
    """
    Creates a Discord embed to display user info.

    :param fields: Tuples of (field_name, value, privacy)
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

    embed = discord.Embed(title=f'Your info', color=EMBED_COLOR)
    embed.add_field(name='Field', value='\n'.join(field_names), inline=True)
    embed.add_field(name='Value', value='\n'.join(values), inline=True)
    embed.add_field(name='Privacy', value='\n'.join(privacies), inline=True)
    return embed


class DatabaseUnavailable(commands.CheckFailure):
    pass


def is_database_available():
    async def predicate(ctx: commands.Context):
        # noinspection PyProtectedMember
        db_connected = cast(UserData, ctx.cog).database.connected()
        if not db_connected:
            raise DatabaseUnavailable()
        return True
    return commands.check(predicate)


error_msgs: Dict[Type[Exception], str] = {
    commands.PrivateMessageOnly:
        'For your privacy, DM me to use this command.',
    DatabaseUnavailable:
        'Unable to access database.',
}


class UserData(commands.Cog):

    database: Database = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def set_database_adapter(self, database: Database):
        self.database = database

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context,
                               error: commands.CommandError):
        try:
            msg = error_msgs[type(error)]
        except KeyError:
            logger.warning(f'Unexpected error: {error}')
            msg = 'Unexpected error.'
        embed = discord.Embed(title='Error', description=msg, color=0xff0000)
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @is_database_available()
    @commands.dm_only()
    async def bio(self, ctx: commands.Context):
        """Displays your personal info"""

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
        embed = make_embed(
            ('Name', preferred_name, privacy_preferred_name),
            ('Pronouns', pronouns, privacy_pronouns),
            ('Birthday', birthday, privacy_birthday),
            ('Age', age, privacy_age),
            ('Timezone', timezone, privacy_timezone),
        )
        await ctx.send(embed=embed)

    @bio.command()
    @is_database_available()
    @commands.dm_only()
    async def clear(self, ctx: commands.Context):
        """Deletes all of your personal info"""
        user_id: int = ctx.author.id
        self.database.clear_data(user_id)

    @bio.command()
    @is_database_available()
    @commands.dm_only()
    async def name(self, ctx: commands.Context, new_name: Optional[str]):
        user_id: int = ctx.author.id
        if new_name is None:
            # Get value
            preferred_name = self.database.get_preferred_name(user_id)
            privacy = self.database.get_privacy_preferred_name(user_id)
            embed = make_embed(('Name', preferred_name, privacy))
            await ctx.send(embed=embed)
        else:
            # Set value
            self.database.set_preferred_name(user_id, new_name)

    @commands.command(name='who is')
    @is_database_available()
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
