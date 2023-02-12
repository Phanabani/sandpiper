__all__ = ["pronouns_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class PronounsGroup(app_commands.Group):
    """
    Commands for managing your pronouns
    """

    pass


pronouns_group = PronounsGroup(name="pronouns")
