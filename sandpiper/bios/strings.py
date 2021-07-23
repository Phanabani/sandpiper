from typing import Any

import discord
from discord.ext import commands

from sandpiper.common.discord import find_user_in_mutual_guilds
from sandpiper.common.misc import join
from sandpiper.user_data import Database, PrivacyType

__all__ = [
    'BirthdayExplanations',
    'info_str', 'user_info_str', 'user_names_str',
]

privacy_emojis = {
    PrivacyType.PRIVATE: '⛔',
    PrivacyType.PUBLIC: '✅'
}


class BirthdayExplanations:

    birthday_is_private_soft_suggest = (
        "I can announce when it's your birthday if you change your birthday "
        "privacy to public: `privacy birthday public`"
    )
    birthday_is_private = (
        "I will **not** announce when it's your birthday. You can change this "
        "by setting your birthday to public: `privacy birthday public`"
    )
    birthday_is_public = (
        "I **will** announce when it's your birthday. You can change this by "
        "setting your birthday to private: `privacy birthday private`"
    )
    age_is_private = (
        "I will **not** show your age in your birthday announcement. You can "
        "change this by setting your age to public: `privacy age public`"
    )
    age_is_public = (
        "I **will** show your age in your birthday announcement. You can "
        "change this by setting your age to private: `privacy age private`"
    )


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
