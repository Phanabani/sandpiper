__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from .pronouns_group import pronouns_group
from .._common.discord import get_id_and_db
from ...strings import user_info_str

logger = logging.getLogger(__name__)


@pronouns_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display your pronouns
    """
    user_id, db = await get_id_and_db(inter)

    pronouns = await db.get_pronouns(user_id)
    privacy = await db.get_privacy_pronouns(user_id)
    await InfoEmbed(user_info_str("Pronouns", pronouns, privacy)).send(inter)
