__all__ = ["birthday_channel_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class BirthdayChannelGroup(app_commands.Group):
    """
    Commands for managing the birthday notification channel
    """

    pass


# Admins only
birthday_channel_group = BirthdayChannelGroup(
    name="birthday-channel", default_permissions=None, guild_only=True
)
