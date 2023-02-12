__all__ = ["timezone_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class TimezoneGroup(app_commands.Group):
    """
    Commands for managing your timezone
    """

    pass


timezone_group = TimezoneGroup(name="timezone")
