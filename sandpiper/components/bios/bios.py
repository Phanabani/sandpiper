__all__ = ["Bios"]

import logging

import discord.ext.commands as commands

from sandpiper.common.component import Component
from . import commands as bios_commands  # noqa

logger = logging.getLogger(__name__)


class Bios(Component):
    """
    Store some info about yourself to help your friends get to know you
    more easily! These commands can be used in DMs with Sandpiper for
    your privacy.

    Some of this info is used by other Sandpiper features, such as
    time conversion and birthday notifications.
    """

    allow_public_setting: bool

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
