from __future__ import annotations

__all__ = ["delete"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .bios_group import bios_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@bios_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete all of your personal info stored in Sandpiper.
    """
    user_id, db = await get_id_and_db(inter)

    await db.delete_user(user_id)
    await SuccessEmbed("Deleted all of your personal info!").send(inter)
