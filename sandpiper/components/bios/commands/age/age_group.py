__all__ = ["age_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class AgeGroup(app_commands.Group):
    """
    Commands for managing your age
    """

    pass


age_group = AgeGroup(name="age")
