import logging
from typing import Any, Dict, Optional, Tuple, Type, cast

import discord
import discord.ext.commands as commands

from .database import Database
from .enums import PrivacyType

__all__ = ['UserData']


logger = logging.getLogger('sandpiper.user_info')


def make_embed(*fields: Tuple[str, Optional[Any], int]):
    """name, value, privacy"""
    for name, value, privacy in fields:
        privacy = PrivacyType(privacy).name.capitalize()
        if value is None:
            value = '*Not set*'
        embed = discord.Embed(title=f'Your info')
        embed.add_field(name=name, value=value, inline=True)
        embed.add_field(name='Privacy', value=privacy, inline=True)
        return embed


class DatabaseUnavailable(commands.CheckFailure):
    pass


def is_database_available():
    async def predicate(ctx: commands.Context):
        # noinspection PyProtectedMember
        db_connected = cast(UserData, ctx.cog)._database.connected()
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

    _database: Database = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def set_database_adapter(self, database: Database):
        self._database = database

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
        preferred_name = self._database.get_preferred_name(user_id)
        privacy_preferred_name = self._database.get_privacy_preferred_name(user_id)
        pronouns = self._database.get_pronouns(user_id)
        privacy_pronouns = self._database.get_privacy_pronouns(user_id)
        birthday = self._database.get_birthday(user_id)
        privacy_birthday = self._database.get_privacy_birthday(user_id)
        age = self._database.get_age(user_id)
        privacy_age = self._database.get_privacy_age(user_id)
        timezone = self._database.get_timezone(user_id)
        privacy_timezone = self._database.get_privacy_timezone(user_id)
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
        self._database.clear_data(user_id)

    @bio.command()
    @is_database_available()
    @commands.dm_only()
    async def name(self, ctx: commands.Context, new_name: Optional[str]):
        user_id: int = ctx.author.id
        if new_name is None:
            # Get value
            preferred_name = self._database.get_preferred_name(user_id)
            privacy = self._database.get_privacy_preferred_name(user_id)
            embed = make_embed(('Name', preferred_name, privacy))
            await ctx.send(embed=embed)
        else:
            # Set value
            self._database.set_preferred_name(user_id, new_name)

    @commands.command(name='who is')
    @is_database_available()
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
