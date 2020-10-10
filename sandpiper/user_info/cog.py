from datetime import date
import logging
from typing import Optional

import discord
import discord.ext.commands as commands
from discord.ext.commands import BadArgument

from ..common.embeds import Embeds
from .database import Database, DatabaseError

__all__ = ['UserData']

logger = logging.getLogger('sandpiper.user_info')


class DatabaseUnavailable(commands.CheckFailure):
    pass


def is_database_available():
    async def predicate(ctx: commands.Context):
        cog: Optional[UserData] = ctx.cog
        if cog is None:
            logger.error(
                f'Command has no associated cog (content={ctx.message.content} '
                f'msg={ctx.message} command={ctx.command})')
            raise commands.CheckFailure('Unexpected error.')
        elif not cog.database.connected():
            raise DatabaseUnavailable()
        return True
    return commands.check(predicate)


def date_handler(date_str: str):
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise commands.BadArgument(
            'Use date format YYYY-MM-DD (example: 1997-08-27)')


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
            if isinstance(error.original, DatabaseUnavailable):
                await Embeds.error(ctx, 'Unable to access database.')
            elif isinstance(error.original, DatabaseError):
                await Embeds.error(ctx, 'Error during database operation.')
            else:
                logger.error(
                    f'Unexpected error (content={ctx.message.content!r} '
                    f'message={ctx.message})', exc_info=error.original)
                await Embeds.error(ctx, 'Unexpected error')
        else:
            await Embeds.error(ctx, str(error))

    @commands.group()
    async def bio(self, ctx: commands.Context):
        """Commands for managing your personal info."""
        pass

    @bio.command(name='clear')
    @is_database_available()
    @commands.dm_only()
    async def bio_clear(self, ctx: commands.Context):
        """Delete all of your personal info."""
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
        pronouns = self.database.get_pronouns(user_id)
        birthday = self.database.get_birthday(user_id)
        age = self.database.get_age(user_id)
        age = age if age is not None else 'N/A'
        timezone = self.database.get_timezone(user_id)
        p_preferred_name = (self.database.get_privacy_preferred_name(user_id)
                            .name.capitalize())
        p_pronouns = (self.database.get_privacy_pronouns(user_id)
                      .name.capitalize())
        p_birthday = (self.database.get_privacy_birthday(user_id)
                      .name.capitalize())
        p_age = (self.database.get_privacy_age(user_id)
                 .name.capitalize())
        p_timezone = (self.database.get_privacy_timezone(user_id)
                      .name.capitalize())
        await Embeds.info(
            ctx, fields=(
                ('Name', f'{preferred_name} `({p_preferred_name})`', False),
                ('Pronouns', f'{pronouns} `({p_pronouns})`', False),
                ('Birthday', f'{birthday} `({p_birthday})`', False),
                ('Age', f'{age} `({p_age})`', False),
                ('Timezone', f'{timezone} `({p_timezone})`', False),
            )
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
            raise BadArgument(f'Name must be 64 characters or less '
                              f'(yours: {len(new_name)}).')
        self.database.set_preferred_name(user_id, new_name)
        await Embeds.success(ctx, 'Name set!')

    # Pronouns

    @bio_show.command(name='pronouns')
    @is_database_available()
    @commands.dm_only()
    async def bio_show_pronouns(self, ctx: commands.Context):
        """Display your pronouns."""
        user_id: int = ctx.author.id
        pronouns = self.database.get_pronouns(user_id)
        privacy = self.database.get_privacy_pronouns(user_id)
        await Embeds.user_info(ctx, ('Pronouns', pronouns, privacy))

    @bio_set.command(name='pronouns')
    @is_database_available()
    @commands.dm_only()
    async def bio_set_pronouns(self, ctx: commands.Context, new_pronouns: str):
        """Set your pronouns."""
        user_id: int = ctx.author.id
        if len(new_pronouns) > 64:
            raise BadArgument(f'Pronouns must be 64 characters or less '
                              f'(yours: {len(new_pronouns)}).')
        self.database.set_pronouns(user_id, new_pronouns)
        await Embeds.success(ctx, 'Pronouns set!')

    # Birthday

    @bio_show.command(name='birthday')
    @is_database_available()
    @commands.dm_only()
    async def bio_show_birthday(self, ctx: commands.Context):
        """Display your birthday."""
        user_id: int = ctx.author.id
        birthday = str(self.database.get_birthday(user_id))
        privacy = self.database.get_privacy_birthday(user_id)
        await Embeds.user_info(ctx, ('Birthday', birthday, privacy))

    @bio_set.command(name='birthday')
    @is_database_available()
    @commands.dm_only()
    async def bio_set_birthday(self, ctx: commands.Context,
                               new_birthday: date_handler):
        """Set your birthday."""
        user_id: int = ctx.author.id
        self.database.set_birthday(user_id, new_birthday)
        await Embeds.success(ctx, 'Birthday set!')

    # Other

    @commands.command(name='who is')
    @is_database_available()
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
