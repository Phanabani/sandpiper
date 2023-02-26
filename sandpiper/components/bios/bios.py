__all__ = ["Bios"]

import logging

import discord
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
        self.sandpiper.add_command(bios_commands.whois)

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

    del auto_order
