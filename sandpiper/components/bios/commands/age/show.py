__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from sandpiper.components.bios.strings import user_info_str
from .age_group import age_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@age_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display your age (calculated automatically using your birthday)
    """
    user_id, db = await get_id_and_db(inter)

    age = await db.get_age(user_id)
    age = age if age is not None else "N/A"
    privacy = await db.get_privacy_age(user_id)
    await InfoEmbed(user_info_str("Age", age, privacy)).send(inter)
