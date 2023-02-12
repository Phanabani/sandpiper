__all__ = ["delete"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .name_group import name_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@name_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete your preferred name
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_preferred_name(user_id, None)
    await SuccessEmbed("Preferred name deleted!").send(inter)
