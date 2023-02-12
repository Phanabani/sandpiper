__all__ = ["delete"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .pronouns_group import pronouns_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@pronouns_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete your pronouns
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_pronouns(user_id, None)
    await SuccessEmbed("Pronouns deleted!").send(inter)
