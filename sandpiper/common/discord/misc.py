from __future__ import annotations

__all__ = [
    "MAX_AUTOCOMPLETE_CHOICES",
    "LoggingCommandTree",
    "privacy_handler",
    "cheap_user_hash",
    "find_user_in_mutual_guilds",
    "find_users_by_display_name",
    "find_users_by_username",
    "piper",
]

import logging
from typing import Optional, TYPE_CHECKING, cast

import discord
from discord import Interaction, InteractionType
from discord.app_commands import (
    AppCommandError,
    CheckFailure,
    Command,
    CommandInvokeError,
    CommandTree,
    ContextMenu,
    TransformerError,
)
from discord.ext.commands import BadArgument

from sandpiper.common.embeds import ErrorEmbed, InfoEmbed
from sandpiper.common.exceptions import UserError
from sandpiper.components.user_data import (
    DatabaseError,
    DatabaseUnavailable,
    PrivacyType,
    UserNotInDatabase,
)

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)

MAX_AUTOCOMPLETE_CHOICES = 25


class LoggingCommandTree(CommandTree):
    async def on_error(
        self, interaction: Interaction, error: AppCommandError, /
    ) -> None:
        inter = interaction

        if isinstance(error, CommandInvokeError):
            error = error.original
        elif isinstance(error, TransformerError):
            error = error.__cause__

        if isinstance(error, DatabaseUnavailable):
            embed = ErrorEmbed(str(DatabaseUnavailable))

        elif isinstance(error, UserNotInDatabase):
            # This user has no row in the database
            embed = InfoEmbed(
                "You have no data stored with me. Use the `help` command "
                "to see all available commands!"
            )

        elif isinstance(error, DatabaseError):
            embed = ErrorEmbed("Error during database operation.")

        elif isinstance(error, (UserError, CheckFailure)):
            embed = ErrorEmbed(str(error))

        else:
            logger.error(
                f'Unexpected error in "{inter.command.name}" (data={inter.data})',
                exc_info=error,
            )
            embed = ErrorEmbed("Unexpected error.")

        await embed.send(inter)

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        # Log interaction
        inter = interaction

        if not inter.type == InteractionType.application_command:
            return True

        if isinstance(inter.command, (Command, ContextMenu)):
            logging.getLogger(inter.command.module).info(
                f'Executing command "{inter.command.name}" (author={inter.user} '
                f"data={inter.data})"
            )
        return True


def cheap_user_hash(user_id: int) -> int:
    return user_id >> 22


def privacy_handler(privacy_str: str) -> PrivacyType:
    privacy_str = privacy_str.upper()
    try:
        return PrivacyType[privacy_str]
    except KeyError:
        privacy_names = [n.lower() for n in PrivacyType.__members__.keys()]
        raise BadArgument(f"Privacy must be one of {privacy_names}")


def find_user_in_mutual_guilds(
    client: discord.Client,
    whos_looking: int,
    for_whom: int,
    *,
    short_circuit: bool = False,
) -> list[discord.Member]:
    """
    Find a user who shares mutual guild's with someone else.

    :param client: the client with access to guild members
    :param whos_looking: the source user who is looking for the target
    :param for_whom: the target user being searched for
    :param short_circuit: whether to return on the first found member
    :return: a list of guild members representing the target user
    """
    found_members = []
    for g in client.guilds:
        g: discord.Guild
        if g.get_member(whos_looking):
            member = g.get_member(for_whom)
            if member:
                if short_circuit:
                    return [member]
                found_members.append(member)
    return found_members


def find_users_by_username(
    client: discord.Client, name: str
) -> [list[tuple[int, str]]]:
    """
    Search for users by their Discord username.

    :param client: the client with access to users
    :param name: the substring to search for
    :return: a list of users whose names match
    """
    users = []
    name = name.casefold()
    for user in client.users:
        user: discord.User
        if name in f"{user.name.casefold()}#{user.discriminator}":
            users.append((user.id, f"{user.name}#{user.discriminator}"))
    return users


def find_users_by_display_name(
    client: discord.Client,
    whos_looking: int,
    name: str,
    *,
    guild: Optional[discord.Guild] = None,
) -> [list[tuple[int, str]]]:
    """
    Search for users by their display name (nickname in a guild). You may pass
    in a guild to optimize the search by limiting to only that guild.

    :param client: the client with access to guild members
    :param whos_looking: the user who is searching
    :param name: a substring to search for in user display names
    :param guild: an optional guild to limit the search to
    :return: a list of tuples of (user_id, display_name) with matching users
    """

    users = []
    name = name.casefold()

    def search_guild(guild: discord.Guild):
        if not guild.get_member(whos_looking):
            return
        for member in guild.members:
            member: discord.Member
            if name in member.display_name.casefold():
                users.append((member.id, member.display_name))

    if guild:
        search_guild(guild)
    else:
        for guild in client.guilds:
            search_guild(guild)

    return users


def piper(client_or_interaction: discord.Client | discord.Interaction) -> Sandpiper:
    """Cast a client to Sandpiper"""
    if isinstance(client_or_interaction, discord.Interaction):
        client_or_interaction = client_or_interaction.client
    return cast("Sandpiper", client_or_interaction)
