__all__ = ["pronouns"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.user_data import PrivacyType
from .privacy_group import privacy_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@privacy_group.command()
async def pronouns(inter: discord.Interaction, new_privacy: PrivacyType) -> None:
    """
    Set the privacy of your pronouns to either 'private' or 'public'
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_privacy_pronouns(user_id, new_privacy)
    await SuccessEmbed("Pronouns privacy set!").send(inter)
