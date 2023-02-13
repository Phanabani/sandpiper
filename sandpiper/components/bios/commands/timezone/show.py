__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from sandpiper.components.bios.strings import user_info_str
from .timezone_group import timezone_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@timezone_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display your timezone
    """
    user_id, db = await get_id_and_db(inter)

    timezone = await db.get_timezone(user_id)
    privacy = await db.get_privacy_timezone(user_id)
    await InfoEmbed(user_info_str("Timezone", timezone, privacy)).send(inter)
