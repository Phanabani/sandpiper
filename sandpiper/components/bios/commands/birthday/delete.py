__all__ = ["delete"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .birthday_group import birthday_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@birthday_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete your birthday
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_birthday(user_id, None)
    await SuccessEmbed("Birthday deleted!").send(inter)
