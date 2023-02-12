__all__ = ["birthday_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class BirthdayGroup(app_commands.Group):
    """
    Commands for managing your birthday
    """

    pass


birthday_group = BirthdayGroup(name="birthday")
