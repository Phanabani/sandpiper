from datetime import date
import logging
from typing import Any, Optional

import discord
import discord.ext.commands as commands
from discord.ext.commands import BadArgument

from ..common.embeds import Embeds
from ..user_info.cog import UserData, DatabaseUnavailable
from ..user_info.database import Database, DatabaseError
from ..user_info.enums import PrivacyType

__all__ = ['Bios']

logger = logging.getLogger('sandpiper.bios')

privacy_emojis = {
    PrivacyType.PRIVATE: '⛔',
    PrivacyType.PUBLIC: '✅'
}


def user_info_str(field_name: str, value: Any, privacy: PrivacyType):
    privacy_emoji = privacy_emojis[privacy]
    privacy = privacy.name.capitalize()
    return f'{privacy_emoji} `{privacy:7}` | **{field_name}** • {value}'


def date_handler(date_str: str):
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise commands.BadArgument(
            'Use date format YYYY-MM-DD (example: 1997-08-27)')


class Bios(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return user_data.get_database()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context,
                               error: commands.CommandError):
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, DatabaseUnavailable):
                await Embeds.error(ctx, str(DatabaseUnavailable))
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
    @commands.dm_only()
    async def bio_clear(self, ctx: commands.Context):
        """Delete all of your personal info."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.clear_data(user_id)

    @bio.group(name='show', invoke_without_command=True)
    @commands.dm_only()
    async def bio_show(self, ctx: commands.Context):
        """
        Commands for displaying your personal info. Can be run on its own to
        display all stored info.
        """

        user_id: int = ctx.author.id
        db = self._get_database()

        preferred_name = db.get_preferred_name(user_id)
        pronouns = db.get_pronouns(user_id)
        birthday = db.get_birthday(user_id)
        age = db.get_age(user_id)
        age = age if age is not None else 'N/A'
        timezone = db.get_timezone(user_id)

        p_preferred_name = db.get_privacy_preferred_name(user_id)
        p_pronouns = db.get_privacy_pronouns(user_id)
        p_birthday = db.get_privacy_birthday(user_id)
        p_age = db.get_privacy_age(user_id)
        p_timezone = db.get_privacy_timezone(user_id)

        await Embeds.info(ctx, message=(
            user_info_str('Name', preferred_name, p_preferred_name),
            user_info_str('Pronouns', pronouns, p_pronouns),
            user_info_str('Birthday', birthday, p_birthday),
            user_info_str('Age', age, p_age),
            user_info_str('Timezone', timezone, p_timezone)
        ))

    @bio.group(name='set', invoke_without_command=False)
    async def bio_set(self, ctx: commands.Context):
        """Commands for setting your personal info."""
        pass

    # Name

    @bio_show.command(name='name')
    @commands.dm_only()
    async def bio_show_name(self, ctx: commands.Context):
        """Display your preferred name."""
        user_id: int = ctx.author.id
        db = self._get_database()
        preferred_name = db.get_preferred_name(user_id)
        privacy = db.get_privacy_preferred_name(user_id)
        await Embeds.info(ctx, user_info_str('Name', preferred_name, privacy))

    @bio_set.command(name='name')
    @commands.dm_only()
    async def bio_set_name(self, ctx: commands.Context, new_name: str):
        """Set your preferred name."""
        user_id: int = ctx.author.id
        db = self._get_database()
        if len(new_name) > 64:
            raise BadArgument(f'Name must be 64 characters or less '
                              f'(yours: {len(new_name)}).')
        db.set_preferred_name(user_id, new_name)
        await Embeds.success(ctx, 'Name set!')

    # Pronouns

    @bio_show.command(name='pronouns')
    @commands.dm_only()
    async def bio_show_pronouns(self, ctx: commands.Context):
        """Display your pronouns."""
        user_id: int = ctx.author.id
        db = self._get_database()
        pronouns = db.get_pronouns(user_id)
        privacy = db.get_privacy_pronouns(user_id)
        await Embeds.info(ctx, user_info_str('Pronouns', pronouns, privacy))

    @bio_set.command(name='pronouns')
    @commands.dm_only()
    async def bio_set_pronouns(self, ctx: commands.Context, new_pronouns: str):
        """Set your pronouns."""
        user_id: int = ctx.author.id
        db = self._get_database()
        if len(new_pronouns) > 64:
            raise BadArgument(f'Pronouns must be 64 characters or less '
                              f'(yours: {len(new_pronouns)}).')
        db.set_pronouns(user_id, new_pronouns)
        await Embeds.success(ctx, 'Pronouns set!')

    # Birthday

    @bio_show.command(name='birthday')
    @commands.dm_only()
    async def bio_show_birthday(self, ctx: commands.Context):
        """Display your birthday."""
        user_id: int = ctx.author.id
        db = self._get_database()
        birthday = db.get_birthday(user_id)
        privacy = db.get_privacy_birthday(user_id)
        await Embeds.info(ctx, user_info_str('Birthday', birthday, privacy))

    @bio_set.command(name='birthday')
    @commands.dm_only()
    async def bio_set_birthday(self, ctx: commands.Context,
                               new_birthday: date_handler):
        """Set your birthday."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_birthday(user_id, new_birthday)
        await Embeds.success(ctx, 'Birthday set!')

    # Age

    @bio_show.command(name='age')
    @commands.dm_only()
    async def bio_show_age(self, ctx: commands.Context):
        """Display your age (calculated automatically using your birthday)."""
        user_id: int = ctx.author.id
        db = self._get_database()
        age = db.get_age(user_id)
        privacy = db.get_privacy_age(user_id)
        await Embeds.info(ctx, user_info_str('Age', age, privacy))

    # noinspection PyUnusedLocal
    @bio_set.command(name='age')
    @commands.dm_only()
    async def bio_set_age(self, ctx: commands.Context, new_age: str):
        """
        Age is automatically calculated using your birthday. This command
        exists only to let you know that you don't have to set it.
        """
        await Embeds.error(ctx, 'Age is automatically calculated using your '
                                'birthday. You don\'t need to set it!')

    # Other

    @commands.command(name='who is')
    async def who_is(self, ctx: commands.Context, user: discord.Member):
        pass
