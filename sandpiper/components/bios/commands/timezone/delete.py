__all__ = ["delete"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .timezone_group import timezone_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@timezone_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete your timezone
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_timezone(user_id, None)
    await SuccessEmbed("Timezone deleted!").send(inter)
