__all__ = ["name"]

import logging

import discord

from sandpiper.common.discord import piper
from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.user_data import PrivacyType
from .privacy_group import privacy_group

logger = logging.getLogger(__name__)


@privacy_group.command()
async def name(inter: discord.Interaction, new_privacy: PrivacyType) -> None:
    """
    Set the privacy of your preferred name to either 'private' or " "'public'
    """
    user_id = inter.user.id
    db = await piper(inter).components.user_data.get_database()
    await db.set_privacy_preferred_name(user_id, new_privacy)
    await SuccessEmbed("Name privacy set!").send(inter)
