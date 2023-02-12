__all__ = ["timezone"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.user_data import PrivacyType
from .privacy_group import privacy_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@privacy_group.command()
async def timezone(inter: discord.Interaction, new_privacy: PrivacyType) -> None:
    """
    Set the privacy of your timezone to either 'private' or 'public'
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_privacy_timezone(user_id, new_privacy)
    await SuccessEmbed("Timezone privacy set!").send(inter)
