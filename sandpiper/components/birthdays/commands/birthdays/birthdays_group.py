__all__ = ["birthdays_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class BirthdaysGroup(app_commands.Group):
    """Commands for viewing birthdays"""

    pass


birthdays_group = BirthdaysGroup(name="birthdays")
