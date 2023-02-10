__all__ = ["bios_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class BiosGroup(app_commands.Group):
    """Commands for viewing birthdays"""

    pass


bios_group = BiosGroup(name="bio")
