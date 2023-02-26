__all__ = ["whois"]

import discord
from discord.app_commands import command

from sandpiper.common.discord import (
    find_user_in_mutual_guilds,
    find_users_by_display_name,
    find_users_by_username,
)
from sandpiper.common.embeds import ErrorEmbed, InfoEmbed
from sandpiper.common.exceptions import UserError
from sandpiper.components.bios.strings import user_names_str
from .._common.discord import get_id_and_db


@command()
async def whois(inter: discord.Interaction, name: str):
    """
    Search for a user by one of their names and see info about them
    """
    if len(name) < 2:
        raise UserError("Name must be at least 2 characters.")

    __, db = await get_id_and_db(inter)

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
            if inter.guild:
                # We're in a guild, so don't allow users from other guilds
                # to be found
                if not inter.guild.get_member(user_id):
                    return True
            else:
                # We're in DMs, so check if the executor shares a guild
                # with the target
                if not find_user_in_mutual_guilds(
                    inter.client, inter.user.id, user_id, short_circuit=True
                ):
                    # Executor doesn't share a guild with target
                    return True
        return False

    for user_id, preferred_name in await db.find_users_by_preferred_name(name):
        # Get preferred names from database
        if should_skip_user(user_id):
            continue
        names = await user_names_str(inter, db, user_id, preferred_name=preferred_name)
        user_strs.append(names)

    for user_id, display_name in find_users_by_display_name(
        inter.client, inter.user.id, name, guild=inter.guild
    ):
        # Get display names from guilds
        # This search function filters out non-mutual-guild users as part
        # of its optimization, so we don't need to do that again
        if should_skip_user(user_id, skip_guild_check=True):
            continue
        names = await user_names_str(inter, db, user_id, display_name=display_name)
        user_strs.append(names)

    for user_id, username in find_users_by_username(inter.client, name):
        # Get usernames from client
        if should_skip_user(user_id):
            continue
        names = await user_names_str(inter, db, user_id, username=username)
        user_strs.append(names)

    if user_strs:
        await InfoEmbed(user_strs).send(inter)
    else:
        await ErrorEmbed("No users found with this name.").send(inter)
