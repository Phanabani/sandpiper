from __future__ import annotations

__all__ = [
    "AutoOrder",
    "LoggingCommandTree",
    "DateTransformer",
    "privacy_handler",
    "cheap_user_hash",
    "find_user_in_mutual_guilds",
    "find_users_by_display_name",
    "find_users_by_username",
    "piper",
]

from datetime import date
import logging
from typing import Optional, TYPE_CHECKING, cast

import discord
from discord import Interaction
from discord.app_commands import (
    AppCommandError,
    Command,
    CommandInvokeError,
    CommandTree,
    ContextMenu,
    Transformer,
)
from discord.ext.commands import BadArgument, Command as ExtCommand

from sandpiper.components.user_data import (
    DatabaseError,
    DatabaseUnavailable,
    PrivacyType,
    UserNotInDatabase,
)
from .embeds import ErrorEmbed, InfoEmbed
from .exceptions import UserError
from .time import parse_date

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)


class AutoOrder:
    """
    Decorate commands/groups with an instance of this class to magically
    order them in definition-order in Sandpiper's help command! You should use
    a new instance of this class for each cog to ensure top-level
    commands/groups get ordered correctly.

    This can also be done manually by adding an ``order`` kwarg in the
    command/group decorator call.

    Technically, it adds an 'order' key to the command's __original_kwargs__
    dict, as this is perhaps the only attribute that persists across command
    copies (commands are apparently copied for each help command invocation,
    therefore we lose any other attributes we may set, like a command.order).
    """

    def __init__(self):
        self.top_level_order = 0

    def __call__(self, command: ExtCommand):
        if command.parent is None:
            # Use state to order these top-level commands since the cog isn't
            # bound yet and therefore we can't query the command count
            order = self.top_level_order
            self.top_level_order += 1
        else:
            # Order by parent's commands count
            order = len(command.parent.commands) - 1

        command.__original_kwargs__["order"] = order
        return command


class LoggingCommandTree(CommandTree):
    async def on_error(
        self, interaction: Interaction, error: AppCommandError, /
    ) -> None:
        inter = interaction

        if not isinstance(error, CommandInvokeError):
            await ErrorEmbed(str(error)).send(inter)
            return

        if isinstance(error.original, DatabaseUnavailable):
            embed = ErrorEmbed(str(DatabaseUnavailable))

        elif isinstance(error.original, UserNotInDatabase):
            # This user has no row in the database
            embed = InfoEmbed(
                "You have no data stored with me. Use the `help` command "
                "to see all available commands!"
            )

        elif isinstance(error.original, DatabaseError):
            embed = ErrorEmbed("Error during database operation.")

        elif isinstance(error.original, UserError):
            embed = ErrorEmbed(str(error.original))

        else:
            logger.error(
                f'Unexpected error in "{inter.command.name}" (data={inter.data})',
                exc_info=error.original,
            )
            embed = ErrorEmbed("Unexpected error.")

        await embed.send(inter)

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        # Log interaction
        inter = interaction
        if isinstance(inter.command, (Command, ContextMenu)):
            logging.getLogger(inter.command.module).info(
                f'Executing command "{inter.command.name}" (author={inter.user} '
                f"data={inter.data})"
            )
        return True


def cheap_user_hash(user_id: int) -> int:
    return user_id >> 22


# noinspection PyAbstractClass,PyMethodMayBeStatic,PyUnusedLocal
class DateTransformer(Transformer):
    async def transform(self, interaction: Interaction, date_str: str) -> date:
        try:
            return parse_date(date_str)
        except ValueError as e:
            logger.info(f"Failed to parse date (str={date_str!r} reason={e})")
            raise UserError(
                "Bad date format. Try something like this: `1997-08-27`, "
                "`31 Oct`, `June 15 2001`"
            )


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
