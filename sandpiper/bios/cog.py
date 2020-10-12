from dataclasses import dataclass
from datetime import date
import logging
from typing import Any, List, Optional, Tuple

import discord
import discord.ext.commands as commands
from discord.ext.commands import BadArgument
from fuzzywuzzy import fuzz
from fuzzywuzzy import process as fuzzy_process
import pytz

from ..common.embeds import Embeds
from ..common.misc import join
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


def date_handler(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise commands.BadArgument(
            'Use date format YYYY-MM-DD (example: 1997-08-27)')


def privacy_handler(privacy_str: str) -> PrivacyType:
    privacy_str = privacy_str.upper()
    try:
        return PrivacyType[privacy_str]
    except KeyError:
        privacy_names = [n.lower() for n in PrivacyType.__members__.keys()]
        raise BadArgument(f'Privacy must be one of {privacy_names}')


@dataclass
class TimezoneMatches:
    matches: List[Tuple[str, int]] = None
    best_match: Optional[pytz.BaseTzInfo] = False
    has_multiple_best_matches: bool = False


def fuzzy_match_timezone(tz_str: str, best_match_threshold=75,
                         lower_score_cutoff=50, limit=5) -> TimezoneMatches:
    """
    Fuzzily match a timezone based on given timezone name.

    :param tz_str: timezone name to fuzzily match in pytz's list of timezones
    :param best_match_threshold: Score from 0-100 that the highest scoring
        match must be greater than to qualify as the best match
    :param lower_score_cutoff: Lower score limit from 0-100 to qualify matches
        for storage in ``TimezoneMatches.matches``
    :param limit: Maximum number of matches to store in
        ``TimezoneMatches.matches``
    """

    # ratio (aka token_sort_ratio) provides the best output.
    # partial_ratio finds substrings, which isn't really what users will be
    # searching by, and the _set_ratio methods are totally unusable.
    matches: List[Tuple[str, int]] = fuzzy_process.extractBests(
        tz_str, pytz.all_timezones, scorer=fuzz.ratio,
        score_cutoff=lower_score_cutoff, limit=limit)
    tz_matches = TimezoneMatches(matches)

    if matches and matches[0][1] >= best_match_threshold:
        # Best match
        tz_matches.best_match = pytz.timezone(matches[0][0])
        if len(matches) > 1 and matches[1][1] == matches[0][1]:
            # There are multiple best matches
            # I think given our inputs and scoring algorithm, this shouldn't
            # ever happen, but I'm leaving it just in case
            tz_matches.has_multiple_best_matches = True
    return tz_matches


def find_user_in_mutual_guilds(client: discord.Client, whos_looking: int,
                               for_whom: int) -> List[discord.Member]:
    found_members = []
    for g in client.guilds:
        g: discord.Guild
        if g.get_member(whos_looking):
            member = g.get_member(for_whom)
            if member:
                found_members.append(member)
    return found_members


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

    @bio.command(name='clear', aliases=('delete',))
    @commands.dm_only()
    async def bio_clear(self, ctx: commands.Context):
        """Delete all of your personal info."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.delete_user(user_id)
        await Embeds.success(ctx, 'Deleted your personal data!')

    @bio.group(name='show', aliases=('get',), invoke_without_command=True)
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

    # Privacy setters

    @bio_set.group(name='privacy', invoke_without_command=False)
    async def bio_set_privacy(self, ctx: commands.Context):
        """Commands for managing the privacy of your personal info."""
        pass

    @bio_set_privacy.command(name='all')
    async def bio_set_privacy_all(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of all of your personal info at once."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_preferred_name(user_id, new_privacy)
        db.set_privacy_pronouns(user_id, new_privacy)
        db.set_privacy_birthday(user_id, new_privacy)
        db.set_privacy_age(user_id, new_privacy)
        db.set_privacy_timezone(user_id, new_privacy)
        await Embeds.success(ctx, 'All privacies set!')

    @bio_set_privacy.command(name='name')
    async def bio_set_privacy_name(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of your preferred name."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_preferred_name(user_id, new_privacy)
        await Embeds.success(ctx, 'Name privacy set!')

    @bio_set_privacy.command(name='pronouns')
    async def bio_set_privacy_pronouns(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of your pronouns."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_pronouns(user_id, new_privacy)
        await Embeds.success(ctx, 'Pronouns privacy set!')

    @bio_set_privacy.command(name='birthday')
    async def bio_set_privacy_birthday(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of your birthday."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_birthday(user_id, new_privacy)
        await Embeds.success(ctx, 'Birthday privacy set!')

    @bio_set_privacy.command(name='age')
    async def bio_set_privacy_age(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of your age."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_age(user_id, new_privacy)
        await Embeds.success(ctx, 'Age privacy set!')

    @bio_set_privacy.command(name='timezone')
    async def bio_set_privacy_timezone(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        """Set the privacy of your timezone."""
        user_id: int = ctx.author.id
        db = self._get_database()
        db.set_privacy_timezone(user_id, new_privacy)
        await Embeds.success(ctx, 'Timezone privacy set!')

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
    async def bio_set_age(self, ctx: commands.Context):
        """
        Age is automatically calculated using your birthday. This command
        exists only to let you know that you don't have to set it.
        """
        await Embeds.error(ctx, 'Age is automatically calculated using your '
                                'birthday. You don\'t need to set it!')

    # Timezone

    @bio_show.command(name='timezone')
    @commands.dm_only()
    async def bio_show_timezone(self, ctx: commands.Context):
        """Display your timezone."""
        user_id: int = ctx.author.id
        db = self._get_database()
        timezone = db.get_timezone(user_id)
        privacy = db.get_privacy_timezone(user_id)
        await Embeds.info(ctx, user_info_str('Timezone', timezone, privacy))

    @bio_set.command(name='timezone')
    @commands.dm_only()
    async def bio_set_timezone(self, ctx: commands.Context,
                               *, new_timezone: str):
        """
        Set your timezone. Typing the name of the nearest major city should be
        good enough, but you can also try your state/country if that doesn't
        work.

        As a last resort, use this website to find your full timezone name:
        http://kevalbhatt.github.io/timezone-picker/
        """

        user_id: int = ctx.author.id
        db = self._get_database()

        tz_matches = fuzzy_match_timezone(
            new_timezone, best_match_threshold=50, lower_score_cutoff=50,
            limit=5
        )
        if not tz_matches.matches:
            # No matches
            raise BadArgument(
                'Timezone provided doesn\'t have any close matches. Try '
                'typing the name of a major city near you or your '
                'state/country name.\n\n'
                'If you\'re stuck, try using this '
                '[timezone picker](http://kevalbhatt.github.io/timezone-picker/).'
            )
        if tz_matches.best_match:
            # Display best match with other possible matches
            db.set_timezone(user_id, tz_matches.best_match)
            await Embeds.success(ctx, message=(
                f'Timezone set to **{tz_matches.best_match}**!',
                tz_matches.matches[1:] and '\nOther possible matches:',
                '\n'.join([f'- {name}' for name, _ in tz_matches.matches[1:]])
            ))
        else:
            # No best match; display other possible matches
            await Embeds.error(ctx, message=(
                'Couldn\'t find a good match for the timezone you entered.',
                '\nPossible matches:',
                '\n'.join([f'- {name}' for name, _ in tz_matches.matches])
            ))

    # Who commands

    @commands.group(name='who', invoke_without_subcommand=False)
    async def who(self, ctx: commands.Context):
        """Commands for viewing other users' info."""
        pass

    @who.command(name='is')
    async def who_is(self, ctx: commands.Context, name: str):
        """
        Search for a user by one of their names. Outputs a list of matching
        users, showing their preferred name, Discord username, and nicknames
        in servers you share with them.
        """
        db = self._get_database()
        bot: commands.Bot = ctx.bot

        user_strs = []
        # Create output strings
        for user_id, preferred_name in db.find_users_by_name(name):

            # Get pronouns
            privacy_pronouns = db.get_privacy_pronouns(user_id)
            if privacy_pronouns == PrivacyType.PUBLIC:
                pronouns = db.get_pronouns(user_id)
            else:
                pronouns = None

            # Get discord username and discriminator
            user: discord.User = bot.get_user(user_id)
            if user is not None:
                username = f'{user.name}#{user.discriminator}'
            else:
                username = '`User not found`'

            # Find the user's nicknames on servers they share with the executor
            # of the who is command
            members = find_user_in_mutual_guilds(ctx.bot, ctx.author.id,
                                                 user_id)
            display_names = ', '.join(m.display_name for m in members)

            user_strs.append(join(
                join(preferred_name, pronouns and f'({pronouns})', sep=' '),
                username, display_names,
                sep=' • '
            ))

        if user_strs:
            await Embeds.info(ctx, message=user_strs)
        else:
            await Embeds.error(ctx, 'No users found with this name.')
