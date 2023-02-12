__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from .name_group import name_group
from .._common.discord import get_id_and_db
from ...strings import user_info_str

logger = logging.getLogger(__name__)


@name_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display your preferred name
    """
    user_id, db = await get_id_and_db(inter)

    preferred_name = await db.get_preferred_name(user_id)
    privacy = await db.get_privacy_preferred_name(user_id)
    await InfoEmbed(user_info_str("Name", preferred_name, privacy)).send(inter)
