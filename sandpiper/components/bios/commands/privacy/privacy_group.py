__all__ = ["privacy_group"]

import logging

from discord import app_commands

logger = logging.getLogger(__name__)


class PrivacyGroup(app_commands.Group):
    """
    Commands for setting the privacy of your personal info
    """

    pass


privacy_group = PrivacyGroup(name="privacy")
