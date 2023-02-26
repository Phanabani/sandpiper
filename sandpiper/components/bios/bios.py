__all__ = ["Bios"]

import logging

import discord.ext.commands as commands

from sandpiper.common.component import Component
from sandpiper.common.discord import *
from sandpiper.components.user_data import *
from . import commands as bios_commands  # noqa

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

    del auto_order
