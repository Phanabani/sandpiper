import logging
from typing import Any, Optional

import discord
import discord.ext.commands as commands
from discord.ext.commands import BadArgument

from .misc import fuzzy_match_timezone
from ..common.discord import *
from ..common.embeds import Embeds
from ..common.misc import join
from ..common.time import format_date
from ..user_data.cog import UserData, DatabaseUnavailable
from ..user_data.database import Database, DatabaseError
from ..user_data.enums import PrivacyType

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


async def user_names_str(ctx: commands.Context, db: Database, user_id: int,
                         preferred_name: str = None, username: str = None):
    """
    Create a string with a user's names (preferred name, Discord username,
    guild display names). You can supply ``preferred_name`` or ``username``
    to optimize the number of operations this function has to perform. There
    is no display_name parameter because this function still needs to find
    the user's display name in ALL guilds, so supplying just the one is useless.
    """

    # Get pronouns
    privacy_pronouns = await db.get_privacy_pronouns(user_id)
    if privacy_pronouns == PrivacyType.PUBLIC:
        pronouns = await db.get_pronouns(user_id)
    else:
        pronouns = None

    # Get preferred name
    if preferred_name is None:
        privacy_preferred_name = await db.get_privacy_preferred_name(user_id)
        if privacy_preferred_name == PrivacyType.PUBLIC:
            preferred_name = await db.get_preferred_name(user_id)
            if preferred_name is None:
                preferred_name = '`No preferred name`'
        else:
            preferred_name = '`No preferred name`'

    # Get discord username and discriminator
    if username is None:
        user: discord.User = ctx.bot.get_user(user_id)
        if user is not None:
            username = f'{user.name}#{user.discriminator}'
        else:
            username = '`User not found`'

    # Find the user's nicknames on servers they share with the executor
    # of the who is command
    members = find_user_in_mutual_guilds(ctx.bot, ctx.author.id, user_id)
    display_names = ', '.join(m.display_name for m in members)

    return join(
        join(preferred_name, pronouns and f'({pronouns})', sep=' '),
        username, display_names,
        sep=' • '
    )


class Bios(commands.Cog):

    _show_aliases = ('get',)
    _set_aliases = ()
    _delete_aliases = ('clear', 'remove')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return await user_data.get_database()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context,
                               error: commands.CommandError):
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, DatabaseUnavailable):
                await Embeds.error(ctx, str(DatabaseUnavailable))
            elif isinstance(error.original, DatabaseError):
                await Embeds.error(ctx, "Error during database operation.")
            else:
                logger.error(
                    f'Unexpected error in "{ctx.command}" ('
                    f'content={ctx.message.content!r} '
                    f'message={ctx.message!r})',
                    exc_info=error.original
                )
                await Embeds.error(ctx, "Unexpected error.")
        else:
            await Embeds.error(ctx, str(error))

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        logger.info(
            f'Running command "{ctx.command}" (author={ctx.author} '
            f'content={ctx.message.content!r})'
        )

    @commands.group(
        brief="Personal info commands.",
        help="Commands for managing all of your personal info at once."
    )
    async def bio(self, ctx: commands.Context):
        pass

    @bio.command(
        name='delete', aliases=_delete_aliases,
        brief="Delete all stored info.",
        help="Delete all of your personal info stored in Sandpiper."
    )
    @commands.dm_only()
    async def bio_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.delete_user(user_id)
        await Embeds.success(ctx, "Deleted all of your personal info!")

    @bio.command(
        name='show', aliases=_show_aliases,
        brief="Show all stored info.",
        help="Display all of your personal info stored in Sandpiper."
    )
    @commands.dm_only()
    async def bio_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()

        preferred_name = await db.get_preferred_name(user_id)
        pronouns = await db.get_pronouns(user_id)
        birthday = await db.get_birthday(user_id)
        birthday = format_date(birthday)
        age = await db.get_age(user_id)
        age = age if age is not None else 'N/A'
        timezone = await db.get_timezone(user_id)

        p_preferred_name = await db.get_privacy_preferred_name(user_id)
        p_pronouns = await db.get_privacy_pronouns(user_id)
        p_birthday = await db.get_privacy_birthday(user_id)
        p_age = await db.get_privacy_age(user_id)
        p_timezone = await db.get_privacy_timezone(user_id)

        await Embeds.info(ctx, message=(
            user_info_str('Name', preferred_name, p_preferred_name),
            user_info_str('Pronouns', pronouns, p_pronouns),
            user_info_str('Birthday', birthday, p_birthday),
            user_info_str('Age', age, p_age),
            user_info_str('Timezone', timezone, p_timezone)
        ))

    # Privacy setters

    @commands.group(
        name='privacy', invoke_without_command=False,
        brief="Personal info privacy commands.",
        help="Commands for setting the privacy of your personal info."
    )
    async def privacy(self, ctx: commands.Context):
        pass

    @privacy.command(
        name='all',
        brief="Set all privacies at once.",
        help=(
            "Set the privacy of all of your personal info at once to either "
            "'private' or 'public'."
            "\n\n"
            "Example: privacy all public"
        )
    )
    async def privacy_all(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_preferred_name(user_id, new_privacy)
        await db.set_privacy_pronouns(user_id, new_privacy)
        await db.set_privacy_birthday(user_id, new_privacy)
        await db.set_privacy_age(user_id, new_privacy)
        await db.set_privacy_timezone(user_id, new_privacy)
        await Embeds.success(ctx, "All privacies set!")

    @privacy.command(
        name='name',
        brief="Set preferred name privacy.",
        help=(
            "Set the privacy of your preferred name 'private' or 'public'."
            "\n\n"
            "Example: privacy name public"
        )
    )
    async def privacy_name(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_preferred_name(user_id, new_privacy)
        await Embeds.success(ctx, "Name privacy set!")

    @privacy.command(
        name='pronouns',
        brief="Set pronouns privacy.",
        help=(
            "Set the privacy of your pronouns to either 'private' or 'public'."
            "\n\n"
            "Example: privacy pronouns public"
        )
    )
    async def privacy_pronouns(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_pronouns(user_id, new_privacy)
        await Embeds.success(ctx, "Pronouns privacy set!")

    @privacy.command(
        name='birthday',
        brief="Set birthday privacy.",
        help=(
            "Set the privacy of your birthday to either 'private' or 'public'."
            "\n\n"
            "Example: privacy birthday public"
        )
    )
    async def privacy_birthday(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_birthday(user_id, new_privacy)
        await Embeds.success(ctx, "Birthday privacy set!")

    @privacy.command(
        name='age',
        brief="Set age privacy.",
        help=(
            "Set the privacy of your age to either 'private' or 'public'."
            "\n\n"
            "Example: privacy age public"
        )
    )
    async def privacy_age(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_age(user_id, new_privacy)
        await Embeds.success(ctx, "Age privacy set!")

    @privacy.command(
        name='timezone',
        brief="Set timezone privacy.",
        help=(
            "Set the privacy of your timezone to either 'private' or 'public'."
            "\n\n"
            "Example: privacy timezone public"
        )
    )
    async def privacy_timezone(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_timezone(user_id, new_privacy)
        await Embeds.success(ctx, "Timezone privacy set!")

    # Name

    @commands.group(
        name='name', invoke_without_command=False,
        brief="Preferred name commands.",
        help="Commands for managing your preferred name."
    )
    async def name(self, ctx: commands.Context):
        pass

    @name.command(
        name='show', aliases=_show_aliases,
        help="Display your preferred name."
    )
    @commands.dm_only()
    async def name_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        preferred_name = await db.get_preferred_name(user_id)
        privacy = await db.get_privacy_preferred_name(user_id)
        await Embeds.info(ctx, user_info_str('Name', preferred_name, privacy))

    @name.command(
        name='set', aliases=_set_aliases,
        brief="Set your preferred name.",
        help=(
             "Set your preferred name. Must be 64 characters or less."
             "\n\n"
             "Example: name set Hawk"
        )
    )
    @commands.dm_only()
    async def name_set(self, ctx: commands.Context, *, new_name: str):
        user_id: int = ctx.author.id
        db = await self._get_database()
        if len(new_name) > 64:
            raise BadArgument(f"Name must be 64 characters or less "
                              f"(yours: {len(new_name)}).")
        await db.set_preferred_name(user_id, new_name)
        await Embeds.success(ctx, "Preferred name set!")

        if await db.get_privacy_preferred_name(user_id) == PrivacyType.PRIVATE:
            await Embeds.warning(
                ctx,
                "Your preferred name is set to private. If you want others to "
                "be able to see it through Sandpiper, set it to public with "
                "the command `privacy name public`."
            )

    @name.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your preferred name."
    )
    @commands.dm_only()
    async def name_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_preferred_name(user_id, None)
        await Embeds.success(ctx, "Preferred name deleted!")

    # Pronouns

    @commands.group(
        name='pronouns', invoke_without_command=False,
        brief="Pronouns commands.",
        help="Commands for managing your pronouns."
    )
    async def pronouns(self, ctx: commands.Context):
        pass

    @pronouns.command(
        name='show', aliases=_show_aliases,
        help="Display your pronouns."
    )
    @commands.dm_only()
    async def pronouns_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        pronouns = await db.get_pronouns(user_id)
        privacy = await db.get_privacy_pronouns(user_id)
        await Embeds.info(ctx, user_info_str('Pronouns', pronouns, privacy))

    @pronouns.command(
        name='set', aliases=_set_aliases,
        brief="Set your pronouns.",
        help=(
            "Set your pronouns. Must be 64 characters or less."
            "\n\n"
            "Example: pronouns set She/Her"
        )
    )
    @commands.dm_only()
    async def pronouns_set(self, ctx: commands.Context, *, new_pronouns: str):
        user_id: int = ctx.author.id
        db = await self._get_database()
        if len(new_pronouns) > 64:
            raise BadArgument(f"Pronouns must be 64 characters or less "
                              f"(yours: {len(new_pronouns)}).")
        await db.set_pronouns(user_id, new_pronouns)
        await Embeds.success(ctx, 'Pronouns set!')

        if await db.get_privacy_pronouns(user_id) == PrivacyType.PRIVATE:
            await Embeds.warning(
                ctx,
                "Your pronouns are set to private. If you want others to be "
                "able to see them through Sandpiper, set them to public with "
                "the command `privacy pronouns public`."
            )

    @pronouns.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your pronouns."
    )
    @commands.dm_only()
    async def pronouns_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_pronouns(user_id, None)
        await Embeds.success(ctx, "Pronouns deleted!")

    # Birthday

    @commands.group(
        name='birthday', invoke_without_command=False,
        brief="Birthday commands.",
        help="Commands for managing your birthday."
    )
    async def birthday(self, ctx: commands.Context):
        pass

    @birthday.command(
        name='show', aliases=_show_aliases,
        help="Display your birthday."
    )
    @commands.dm_only()
    async def birthday_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        birthday = await db.get_birthday(user_id)
        birthday = format_date(birthday)
        privacy = await db.get_privacy_birthday(user_id)
        await Embeds.info(ctx, user_info_str('Birthday', birthday, privacy))

    @birthday.command(
        name='set', aliases=_set_aliases,
        brief="Set your birthday.",
        help=(
            "Set your birthday in the format YYYY-MM-DD."
            "\n\n"
            "Example: birthday set 1997-08-27"
        )
    )
    @commands.dm_only()
    async def birthday_set(self, ctx: commands.Context, *,
                           new_birthday: date_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_birthday(user_id, new_birthday)
        await Embeds.success(ctx, "Birthday set!")

        if await db.get_privacy_birthday(user_id) == PrivacyType.PRIVATE:
            await Embeds.warning(
                ctx,
                "Your birthday is set to private. If you want others to be "
                "able to see it through Sandpiper, set it to public with "
                "the command `privacy birthday public`. If you want others to "
                "know your age but not your birthday, you may set that to "
                "public with the command `privacy age public`."
            )

    @birthday.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your birthday."
    )
    @commands.dm_only()
    async def birthday_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_birthday(user_id, None)
        await Embeds.success(ctx, "Birthday deleted!")

    # Age

    @commands.group(
        name='age', invoke_without_command=False,
        brief="Age commands.",
        help="Commands for managing your age."
    )
    async def age(self, ctx: commands.Context):
        pass

    @age.command(
        name='show', aliases=_show_aliases,
        brief="Display your age.",
        help="Display your age (calculated automatically using your birthday)."
    )
    @commands.dm_only()
    async def age_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        age = await db.get_age(user_id)
        age = age if age is not None else 'N/A'
        privacy = await db.get_privacy_age(user_id)
        await Embeds.info(ctx, user_info_str('Age', age, privacy))

    # noinspection PyUnusedLocal
    @age.command(
        name='set', aliases=_set_aliases,
        brief="This command does nothing.",
        help=(
            "Age is automatically calculated using your birthday. This "
            "command exists only to let you know that you don't have to set it."
        )
    )
    @commands.dm_only()
    async def age_set(self, ctx: commands.Context):
        await Embeds.error(
            ctx,
            "Age is automatically calculated using your birthday. "
            "You don't need to set it!"
        )

    # noinspection PyUnusedLocal
    @age.command(
        name='delete', aliases=_delete_aliases,
        brief="This command does nothing.",
        help=(
            "Age is automatically calculated using your birthday. This command "
            "exists only to let you know that you can only delete your birthday."
        )
    )
    @commands.dm_only()
    async def age_delete(self, ctx: commands.Context):
        await Embeds.error(
            ctx,
            "Age is automatically calculated using your birthday. You can "
            "either delete your birthday with `birthday delete` or set your "
            "age to private so others can't see it with "
            "`privacy age private`."
        )

    # Timezone

    @commands.group(
        name='timezone', invoke_without_command=False,
        brief="Timezone commands.",
        help="Commands for managing your timezone."
    )
    async def timezone(self, ctx: commands.Context):
        pass

    @timezone.command(
        name='show', aliases=_show_aliases,
        help="Display your timezone."
    )
    @commands.dm_only()
    async def timezone_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        timezone = await db.get_timezone(user_id)
        privacy = await db.get_privacy_timezone(user_id)
        await Embeds.info(ctx, user_info_str('Timezone', timezone, privacy))

    @timezone.command(
        name='set', aliases=_set_aliases,
        brief="Set your timezone.",
        help=(
            "Set your timezone. Don't worry about formatting. Typing the "
            "name of the nearest major city should be good enough, but you can "
            "also try your state/country if that doesn't work."
            "\n\n"
            "If you're confused, use this website to find your full timezone "
            "name: http://kevalbhatt.github.io/timezone-picker"
            "\n\n"
            "Example: timezone set new york"
        )
    )
    @commands.dm_only()
    async def timezone_set(self, ctx: commands.Context, *, new_timezone: str):
        user_id: int = ctx.author.id
        db = await self._get_database()

        tz_matches = fuzzy_match_timezone(
            new_timezone, best_match_threshold=50, lower_score_cutoff=50,
            limit=5
        )
        if not tz_matches.matches:
            # No matches
            raise BadArgument(
                "Timezone provided doesn't have any close matches. Try "
                "typing the name of a major city near you or your "
                "state/country name.\n\n"
                "If you're stuck, try using this "
                "[timezone picker](http://kevalbhatt.github.io/timezone-picker/)."
            )

        if tz_matches.best_match:
            # Display best match with other possible matches
            await db.set_timezone(user_id, tz_matches.best_match)
            await Embeds.success(ctx, message=(
                f"Timezone set to **{tz_matches.best_match}**!",
                tz_matches.matches[1:] and "\nOther possible matches:",
                '\n'.join([f'- {name}' for name, _ in tz_matches.matches[1:]])
            ))
        else:
            # No best match; display other possible matches
            await Embeds.error(ctx, message=(
                "Couldn't find a good match for the timezone you entered.",
                "\nPossible matches:",
                '\n'.join([f'- {name}' for name, _ in tz_matches.matches])
            ))

        if await db.get_privacy_timezone(user_id) == PrivacyType.PRIVATE:
            await Embeds.warning(
                ctx,
                "Your timezone is set to private. If you want others to be "
                "able to see it through Sandpiper, set it to public with "
                "the command `privacy timezone public`."
            )

    @timezone.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your timezone."
    )
    @commands.dm_only()
    async def timezone_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_timezone(user_id, None)
        await Embeds.success(ctx, "Timezone deleted!")

    # Extra commands

    @commands.command(
        name='whois',
        brief="Search for a user.",
        help=(
            "Search for a user by one of their names. Outputs a list of "
            "matching users, showing their preferred name, Discord username, "
            "and nicknames in servers you share with them."
            "\n\n"
            "Example: whois hawk"
        )
    )
    async def whois(self, ctx: commands.Context, name: str):
        if len(name) < 2:
            raise BadArgument("Name must be at least 2 characters.")

        db = await self._get_database()

        user_strs = []
        seen_users = set()

        for user_id, preferred_name in await db.find_users_by_preferred_name(name):
            if user_id in seen_users:
                continue
            seen_users.add(user_id)
            names = await user_names_str(ctx, db, user_id,
                                         preferred_name=preferred_name)
            user_strs.append(names)

        for user_id, __ in find_users_by_display_name(
                ctx.bot, ctx.author.id, name):
            if user_id in seen_users:
                continue
            seen_users.add(user_id)
            names = await user_names_str(ctx, db, user_id)
            user_strs.append(names)

        for user_id, username in find_users_by_username(ctx.bot, name):
            if user_id in seen_users:
                continue
            seen_users.add(user_id)
            names = await user_names_str(ctx, db, user_id, username=username)
            user_strs.append(names)

        if user_strs:
            await Embeds.info(ctx, message=user_strs)
        else:
            await Embeds.error(ctx, "No users found with this name.")
