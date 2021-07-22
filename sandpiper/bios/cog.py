import logging
from typing import Any, Optional

import discord
import discord.ext.commands as commands
from discord.ext.commands import BadArgument

from sandpiper.birthdays import Birthdays
from sandpiper.common.discord import *
from sandpiper.common.embeds import Embeds
from sandpiper.common.misc import join
from sandpiper.common.time import format_date, fuzzy_match_timezone
from sandpiper.user_data import *

__all__ = ['Bios']

logger = logging.getLogger('sandpiper.bios')

privacy_emojis = {
    PrivacyType.PRIVATE: '⛔',
    PrivacyType.PUBLIC: '✅'
}


def info_str(field_name: str, value: Any):
    return f"**{field_name}** • {value}"


def user_info_str(field_name: str, value: Any, privacy: PrivacyType):
    privacy_emoji = privacy_emojis[privacy]
    privacy = privacy.name.capitalize()
    return f"{privacy_emoji} `{privacy:7}` | {info_str(field_name, value)}"


async def user_names_str(
        ctx: commands.Context, db: Database, user_id: int,
        *, preferred_name: str = None, username: str = None,
        display_name: str = None
):
    """
    Create a string with a user's names (preferred name, Discord username,
    guild display names). You can supply ``preferred_name``, ``username``,
    or ``display_name`` to optimize the number of operations this function
    has to perform.
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

    if ctx.guild is None:
        # Find the user's nicknames on servers they share with the executor
        # of the whois command
        members = find_user_in_mutual_guilds(ctx.bot, ctx.author.id, user_id)
        display_names = ', '.join(m.display_name for m in members)
    else:
        if display_name is None:
            # Find the user's nickname in the current guild ONLY
            display_names = ctx.guild.get_member(user_id).display_name
        else:
            # Use the passed-in display name
            display_names = display_name

    return join(
        join(preferred_name, pronouns and f'({pronouns})', sep=' '),
        username, display_names,
        sep=' • '
    )


def maybe_dm_only():
    async def predicate(ctx: commands.Context):
        bios: Bios = ctx.cog
        if not bios.allow_public_setting:
            return await commands.dm_only().predicate(ctx)
        return True
    return commands.check(predicate)


class Bios(commands.Cog):

    __cog_cleaned_doc__ = (
        "Store some info about yourself to help your friends get to know you "
        "more easily! These commands can be used in DMs with Sandpiper for "
        "your privacy."
        "\n\n"
        "Some of this info is used by other Sandpiper features, such as "
        "time conversion and birthday notifications."
    )

    _show_aliases = ('get',)
    _set_aliases = ()
    _delete_aliases = ('clear', 'remove')

    auto_order = AutoOrder()

    def __init__(
            self, bot: commands.Bot, *, allow_public_setting: bool = False
    ):
        self.bot = bot
        self.allow_public_setting = allow_public_setting

    async def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return await user_data.get_database()

    @commands.Cog.listener()
    async def on_command_error(
            self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, DatabaseUnavailable):
                await Embeds.error(ctx, str(DatabaseUnavailable))

            elif isinstance(error.original, UserNotInDatabase):
                # This user has no row in the database
                await Embeds.info(
                    ctx,
                    "You have no data stored with me. Use the `help` command "
                    "to see all available commands!"
                )

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

    @commands.Cog.listener('on_command_completion')
    async def notify_birthdays_cog(self, ctx: commands.Context):
        if ctx.command_failed:
            # Not sure if this is possible here but might as well check
            return

        if ctx.command.qualified_name in (
                'birthday set', 'timezone set',
                'privacy all', 'privacy birthday', 'privacy timezone'
        ):
            logger.debug(
                f"Notifying birthdays cog about change from command "
                f"{ctx.command.qualified_name} (user_id={ctx.author.id})"
            )
            birthdays_cog: Birthdays
            birthdays_cog = self.bot.get_cog('Birthdays')
            if birthdays_cog is None:
                logger.debug(
                    "No birthdays cog loaded; skipping change notification"
                )
                return
            await birthdays_cog.notify_change(ctx.author.id)

    @auto_order
    @commands.group(
        brief="Personal info commands.",
        help="Commands for managing all of your personal info at once."
    )
    async def bio(self, ctx: commands.Context):
        pass

    @auto_order
    @bio.command(
        name='show', aliases=_show_aliases,
        brief="Show all stored info.",
        help="Display all of your personal info stored in Sandpiper."
    )
    @maybe_dm_only()
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

    @auto_order
    @bio.command(
        name='delete', aliases=_delete_aliases,
        brief="Delete all stored info.",
        help="Delete all of your personal info stored in Sandpiper."
    )
    @maybe_dm_only()
    async def bio_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.delete_user(user_id)
        await Embeds.success(ctx, "Deleted all of your personal info!")

    # Privacy setters

    @auto_order
    @commands.group(
        name='privacy', invoke_without_command=False,
        brief="Personal info privacy commands.",
        help="Commands for setting the privacy of your personal info."
    )
    async def privacy(self, ctx: commands.Context):
        pass

    @auto_order
    @privacy.command(
        name='all',
        brief="Set all privacies at once.",
        help=(
            "Set the privacy of all of your personal info at once to either "
            "'private' or 'public'."
        ),
        example="privacy all public"
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

    @auto_order
    @privacy.command(
        name='name',
        brief="Set preferred name privacy.",
        help=(
            "Set the privacy of your preferred name to either 'private' or "
            "'public'."
        ),
        example="privacy name public"
    )
    async def privacy_name(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_preferred_name(user_id, new_privacy)
        await Embeds.success(ctx, "Name privacy set!")

    @auto_order
    @privacy.command(
        name='pronouns',
        brief="Set pronouns privacy.",
        help=(
            "Set the privacy of your pronouns to either 'private' or 'public'."
        ),
        example="privacy pronouns public"
    )
    async def privacy_pronouns(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_pronouns(user_id, new_privacy)
        await Embeds.success(ctx, "Pronouns privacy set!")

    @auto_order
    @privacy.command(
        name='birthday',
        brief="Set birthday privacy.",
        help=(
            "Set the privacy of your birthday to either 'private' or 'public'."
        ),
        example="privacy birthday public"
    )
    async def privacy_birthday(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_birthday(user_id, new_privacy)
        await Embeds.success(ctx, "Birthday privacy set!")

    @auto_order
    @privacy.command(
        name='age',
        brief="Set age privacy.",
        help=(
            "Set the privacy of your age to either 'private' or 'public'."
        ),
        example="privacy age public"
    )
    async def privacy_age(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_age(user_id, new_privacy)
        await Embeds.success(ctx, "Age privacy set!")

    @auto_order
    @privacy.command(
        name='timezone',
        brief="Set timezone privacy.",
        help=(
            "Set the privacy of your timezone to either 'private' or 'public'."
        ),
        example="privacy timezone public"
    )
    async def privacy_timezone(
            self, ctx: commands.Context, new_privacy: privacy_handler):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_privacy_timezone(user_id, new_privacy)
        await Embeds.success(ctx, "Timezone privacy set!")

    # Name

    @auto_order
    @commands.group(
        name='name', invoke_without_command=False,
        brief="Preferred name commands.",
        help="Commands for managing your preferred name."
    )
    async def name(self, ctx: commands.Context):
        pass

    @auto_order
    @name.command(
        name='show', aliases=_show_aliases,
        help="Display your preferred name."
    )
    @maybe_dm_only()
    async def name_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        preferred_name = await db.get_preferred_name(user_id)
        privacy = await db.get_privacy_preferred_name(user_id)
        await Embeds.info(ctx, user_info_str('Name', preferred_name, privacy))

    @auto_order
    @name.command(
        name='set', aliases=_set_aliases,
        brief="Set your preferred name.",
        help="Set your preferred name. Must be 64 characters or less.",
        example="name set Hawk"
    )
    @maybe_dm_only()
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

    @auto_order
    @name.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your preferred name."
    )
    @maybe_dm_only()
    async def name_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_preferred_name(user_id, None)
        await Embeds.success(ctx, "Preferred name deleted!")

    # Pronouns

    @auto_order
    @commands.group(
        name='pronouns', invoke_without_command=False,
        brief="Pronouns commands.",
        help="Commands for managing your pronouns."
    )
    async def pronouns(self, ctx: commands.Context):
        pass

    @auto_order
    @pronouns.command(
        name='show', aliases=_show_aliases,
        help="Display your pronouns."
    )
    @maybe_dm_only()
    async def pronouns_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        pronouns = await db.get_pronouns(user_id)
        privacy = await db.get_privacy_pronouns(user_id)
        await Embeds.info(ctx, user_info_str('Pronouns', pronouns, privacy))

    @auto_order
    @pronouns.command(
        name='set', aliases=_set_aliases,
        brief="Set your pronouns.",
        help="Set your pronouns. Must be 64 characters or less.",
        example="pronouns set She/Her"
    )
    @maybe_dm_only()
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

    @auto_order
    @pronouns.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your pronouns."
    )
    @maybe_dm_only()
    async def pronouns_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_pronouns(user_id, None)
        await Embeds.success(ctx, "Pronouns deleted!")

    # Birthday

    @auto_order
    @commands.group(
        name='birthday', invoke_without_command=False,
        brief="Birthday commands.",
        help="Commands for managing your birthday."
    )
    async def birthday(self, ctx: commands.Context):
        pass

    @auto_order
    @birthday.command(
        name='show', aliases=_show_aliases,
        help="Display your birthday."
    )
    @maybe_dm_only()
    async def birthday_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        birthday = await db.get_birthday(user_id)
        birthday = format_date(birthday)
        privacy = await db.get_privacy_birthday(user_id)
        await Embeds.info(ctx, user_info_str('Birthday', birthday, privacy))

    @auto_order
    @birthday.command(
        name='set', aliases=_set_aliases,
        brief="Set your birthday.",
        help=(
            "Set your birthday. There are several allowed formats, and some "
            "allow you to omit your birth year if you are not comfortable with "
            "adding it (your age will not be calculated)."
            "\n\n"
            "See the examples below for valid formats."
        ),
        example=(
            "birthday set 1997-08-27",
            "birthday set 8 August 1997",
            "birthday set Aug 8 1997",
            "birthday set August 8",
            "birthday set 8 Aug",
        )
    )
    @maybe_dm_only()
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

    @auto_order
    @birthday.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your birthday."
    )
    @maybe_dm_only()
    async def birthday_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_birthday(user_id, None)
        await Embeds.success(ctx, "Birthday deleted!")

    # Age

    @auto_order
    @commands.group(
        name='age', invoke_without_command=False,
        brief="Age commands.",
        help="Commands for managing your age."
    )
    async def age(self, ctx: commands.Context):
        pass

    @auto_order
    @age.command(
        name='show', aliases=_show_aliases,
        brief="Display your age.",
        help="Display your age (calculated automatically using your birthday)."
    )
    @maybe_dm_only()
    async def age_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        age = await db.get_age(user_id)
        age = age if age is not None else 'N/A'
        privacy = await db.get_privacy_age(user_id)
        await Embeds.info(ctx, user_info_str('Age', age, privacy))

    # noinspection PyUnusedLocal
    @auto_order
    @age.command(
        name='set', aliases=_set_aliases, hidden=True,
        brief="This command does nothing.",
        help=(
            "Age is automatically calculated using your birthday. This "
            "command exists only to let you know that you don't have to set it."
        )
    )
    @maybe_dm_only()
    async def age_set(self, ctx: commands.Context):
        await Embeds.error(
            ctx,
            "Age is automatically calculated using your birthday. "
            "You don't need to set it!"
        )

    # noinspection PyUnusedLocal
    @auto_order
    @age.command(
        name='delete', aliases=_delete_aliases, hidden=True,
        brief="This command does nothing.",
        help=(
            "Age is automatically calculated using your birthday. This command "
            "exists only to let you know that you can only delete your birthday."
        )
    )
    @maybe_dm_only()
    async def age_delete(self, ctx: commands.Context):
        await Embeds.error(
            ctx,
            "Age is automatically calculated using your birthday. You can "
            "either delete your birthday with `birthday delete` or set your "
            "age to private so others can't see it with "
            "`privacy age private`."
        )

    # Timezone

    @auto_order
    @commands.group(
        name='timezone', invoke_without_command=False,
        brief="Timezone commands.",
        help="Commands for managing your timezone."
    )
    async def timezone(self, ctx: commands.Context):
        pass

    @auto_order
    @timezone.command(
        name='show', aliases=_show_aliases,
        help="Display your timezone."
    )
    @maybe_dm_only()
    async def timezone_show(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        timezone = await db.get_timezone(user_id)
        privacy = await db.get_privacy_timezone(user_id)
        await Embeds.info(ctx, user_info_str('Timezone', timezone, privacy))

    @auto_order
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
        ),
        example=(
            "timezone set America/New_York",
            "timezone set new york",
            "timezone set amsterdam",
            "timezone set london",
        )
    )
    @maybe_dm_only()
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

    @auto_order
    @timezone.command(
        name='delete', aliases=_delete_aliases,
        help="Delete your timezone."
    )
    @maybe_dm_only()
    async def timezone_delete(self, ctx: commands.Context):
        user_id: int = ctx.author.id
        db = await self._get_database()
        await db.set_timezone(user_id, None)
        await Embeds.success(ctx, "Timezone deleted!")

    # region Server commands

    @auto_order
    @commands.group(
        name='server', invoke_without_command=False,
        brief="Server commands. (admin only)",
        help="Commands for managing server settings. (admin only)"
    )
    async def server(self, ctx: commands.Context):
        pass

    # region Birthday channel

    @auto_order
    @server.group(
        name='birthday_channel', invoke_without_command=False,
        brief="Birthday notification channel commands",
        help=(
            "Commands for managing the birthday notification channel"
        )
    )
    async def server_birthday_channel(self, ctx: commands.Context):
        pass

    @auto_order
    @server_birthday_channel.command(
        name='show', aliases=_show_aliases,
        brief="Show the birthday notification channel",
        help=(
            "Show the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        )
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_show(self, ctx: commands.Context):
        guild_id: int = ctx.guild.id
        db = await self._get_database()

        bday_channel_id = await db.get_guild_birthday_channel(guild_id)
        if bday_channel_id is None:
            await Embeds.info(ctx, info_str("Birthday channel", "N/A"))
            return

        await Embeds.info(ctx, info_str(
            "Birthday channel", f"<#{bday_channel_id}> (id={bday_channel_id})"
        ))

    @auto_order
    @server_birthday_channel.command(
        name='set', aliases=_set_aliases,
        brief="Set the birthday notification channel",
        help=(
            "Set the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        )
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_set(
            self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        guild_id: int = ctx.guild.id
        db = await self._get_database()
        await db.set_guild_birthday_channel(guild_id, new_channel.id)
        await Embeds.success(ctx, "Birthday channel set!")

    @auto_order
    @server_birthday_channel.command(
        name='delete', aliases=_delete_aliases,
        brief="Delete the birthday notification channel",
        help=(
            "Delete the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        )
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_delete(self, ctx: commands.Context):
        guild_id: int = ctx.guild.id
        db = await self._get_database()
        await db.set_guild_birthday_channel(guild_id, None)
        await Embeds.success(ctx, "Birthday channel deleted!")

    # endregion
    # endregion

    # Extra commands

    @auto_order
    @commands.command(
        name='whois',
        brief="Search for a user.",
        help=(
            "Search for a user by one of their names. Outputs a list of "
            "matching users, showing their preferred name, Discord username, "
            "and nicknames in servers you share with them."
        ),
        example="whois hawk"
    )
    async def whois(self, ctx: commands.Context, *, name: str):
        if len(name) < 2:
            raise BadArgument("Name must be at least 2 characters.")

        db = await self._get_database()

        user_strs = []
        seen_users = set()

        def should_skip_user(user_id: int, *, skip_guild_check=False):
            """
            Filter out users that have already been seen or who aren't in the
            guild.

            :param user_id: the target user that's been found by the search
                functions
            :param skip_guild_check: whether to skip the process of ensuring
                the target and executor exist in mutual guilds (for
                optimization)
            """
            if user_id in seen_users:
                return True
            seen_users.add(user_id)
            if not skip_guild_check:
                if ctx.guild:
                    # We're in a guild, so don't allow users from other guilds
                    # to be found
                    if not ctx.guild.get_member(user_id):
                        return True
                else:
                    # We're in DMs, so check if the executor shares a guild
                    # with the target
                    if not find_user_in_mutual_guilds(
                            ctx.bot, ctx.author.id, user_id,
                            short_circuit=True):
                        # Executor doesn't share a guild with target
                        return True
            return False

        for user_id, preferred_name in await db.find_users_by_preferred_name(name):
            # Get preferred names from database
            if should_skip_user(user_id):
                continue
            names = await user_names_str(
                ctx, db, user_id, preferred_name=preferred_name
            )
            user_strs.append(names)

        for user_id, display_name in find_users_by_display_name(
                ctx.bot, ctx.author.id, name, guild=ctx.guild):
            # Get display names from guilds
            # This search function filters out non-mutual-guild users as part
            # of its optimization, so we don't need to do that again
            if should_skip_user(user_id, skip_guild_check=True):
                continue
            names = await user_names_str(
                ctx, db, user_id, display_name=display_name
            )
            user_strs.append(names)

        for user_id, username in find_users_by_username(ctx.bot, name):
            # Get usernames from client
            if should_skip_user(user_id):
                continue
            names = await user_names_str(
                ctx, db, user_id, username=username
            )
            user_strs.append(names)

        if user_strs:
            await Embeds.info(ctx, message=user_strs)
        else:
            await Embeds.error(ctx, "No users found with this name.")

    del auto_order
