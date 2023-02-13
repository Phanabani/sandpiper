__all__ = ["Bios"]

import logging

import discord
from discord.ext.commands import BadArgument
import discord.ext.commands as commands

from sandpiper.common.component import Component
from sandpiper.common.discord import *
from sandpiper.common.embeds import *
from sandpiper.components.user_data import *
from . import commands as bios_commands  # noqa
from .strings import *

logger = logging.getLogger(__name__)


def maybe_dm_only():
    async def predicate(ctx: commands.Context):
        bios: Bios = ctx.cog
        if not bios.allow_public_setting:
            return await commands.dm_only().predicate(ctx)
        return True

    return commands.check(predicate)


class Bios(Component):
    """
    Store some info about yourself to help your friends get to know you
    more easily! These commands can be used in DMs with Sandpiper for
    your privacy.

    Some of this info is used by other Sandpiper features, such as
    time conversion and birthday notifications.
    """

    allow_public_setting: bool

    _show_aliases = ("get",)
    _set_aliases = ()
    _delete_aliases = ("clear", "remove")

    auto_order = AutoOrder()

    async def setup(self):
        logger.debug("Setting up")

        config = self.sandpiper.config.components.bios
        self.allow_public_setting = config.allow_public_setting

        self.sandpiper.add_command(bios_commands.bios_group)
        self.sandpiper.add_command(bios_commands.privacy_group)
        self.sandpiper.add_command(bios_commands.name_group)
        self.sandpiper.add_command(bios_commands.pronouns_group)
        self.sandpiper.add_command(bios_commands.birthday_group)
        self.sandpiper.add_command(bios_commands.age_group)
        self.sandpiper.add_command(bios_commands.timezone_group)
        self.sandpiper.add_command(bios_commands.birthday_channel_group)

        logger.debug("Setup complete")

    async def _get_database(self) -> Database:
        user_data = self.sandpiper.components.user_data
        if user_data is None:
            raise RuntimeError("UserData cog is not loaded.")
        return await user_data.get_database()

    @commands.Cog.listener("on_command_completion")
    async def notify_birthdays_component(self, ctx: commands.Context):
        if ctx.command_failed:
            # Not sure if this is possible here but might as well check
            return

        if ctx.command.qualified_name in (
            "birthday set",
            "timezone set",
            "privacy all",
            "privacy birthday",
            "privacy timezone",
        ):
            logger.debug(
                f"Notifying birthdays cog about change from command "
                f"{ctx.command.qualified_name} (user_id={ctx.author.id})"
            )
            birthdays = self.sandpiper.components.birthdays
            if birthdays is None:
                logger.debug("No birthdays cog loaded; skipping change notification")
                return
            await birthdays.notify_change(ctx.author.id)

    # region Server commands

    @auto_order
    @commands.group(
        name="server",
        invoke_without_command=False,
        brief="Server commands. (admin only)",
        help="Commands for managing server settings. (admin only)",
    )
    async def server(self, ctx: commands.Context):
        pass

    # region Birthday channel

    @auto_order
    @server.group(
        name="birthday_channel",
        invoke_without_command=False,
        brief="Birthday notification channel commands",
        help="Commands for managing the birthday notification channel",
    )
    async def server_birthday_channel(self, ctx: commands.Context):
        pass

    @auto_order
    @server_birthday_channel.command(
        name="show",
        aliases=_show_aliases,
        brief="Show the birthday notification channel",
        help=(
            "Show the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        ),
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_show(self, ctx: commands.Context):
        guild_id: int = ctx.guild.id
        db = await self._get_database()

        bday_channel_id = await db.get_guild_birthday_channel(guild_id)
        if bday_channel_id is None:
            await InfoEmbed(info_str("Birthday channel", "N/A")).send(ctx)
            return

        await InfoEmbed(
            info_str("Birthday channel", f"<#{bday_channel_id}> (id={bday_channel_id})")
        ).send(ctx)

    @auto_order
    @server_birthday_channel.command(
        name="set",
        aliases=_set_aliases,
        brief="Set the birthday notification channel",
        help=(
            "Set the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        ),
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_set(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        guild_id: int = ctx.guild.id
        db = await self._get_database()
        await db.set_guild_birthday_channel(guild_id, new_channel.id)
        await SuccessEmbed("Birthday channel set!").send(ctx)

    @auto_order
    @server_birthday_channel.command(
        name="delete",
        aliases=_delete_aliases,
        brief="Delete the birthday notification channel",
        help=(
            "Delete the birthday notification channel in your server. This is "
            "where Sandpiper will send messages when it's someone's birthday."
        ),
    )
    @commands.has_guild_permissions(administrator=True)
    async def server_birthday_channel_delete(self, ctx: commands.Context):
        guild_id: int = ctx.guild.id
        db = await self._get_database()
        await db.set_guild_birthday_channel(guild_id, None)
        await SuccessEmbed("Birthday channel deleted!").send(ctx)

    # endregion
    # endregion

    # Extra commands

    @auto_order
    @commands.command(
        name="whois",
        brief="Search for a user.",
        help=(
            "Search for a user by one of their names. Outputs a list of "
            "matching users, showing their preferred name, Discord username, "
            "and nicknames in servers you share with them."
        ),
        example="whois phana",
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
                        ctx.bot, ctx.author.id, user_id, short_circuit=True
                    ):
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
            ctx.bot, ctx.author.id, name, guild=ctx.guild
        ):
            # Get display names from guilds
            # This search function filters out non-mutual-guild users as part
            # of its optimization, so we don't need to do that again
            if should_skip_user(user_id, skip_guild_check=True):
                continue
            names = await user_names_str(ctx, db, user_id, display_name=display_name)
            user_strs.append(names)

        for user_id, username in find_users_by_username(ctx.bot, name):
            # Get usernames from client
            if should_skip_user(user_id):
                continue
            names = await user_names_str(ctx, db, user_id, username=username)
            user_strs.append(names)

        if user_strs:
            await InfoEmbed(user_strs).send(ctx)
        else:
            await ErrorEmbed("No users found with this name.").send(ctx)

    del auto_order
