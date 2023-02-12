__all__ = ["name_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class NameGroup(app_commands.Group):
    """
    Commands for managing your preferred name
    """

    pass


name_group = NameGroup(name="name")
