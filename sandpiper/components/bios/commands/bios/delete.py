from __future__ import annotations

__all__ = ["delete"]

import logging

import discord

from sandpiper.common.discord import piper
from sandpiper.common.embeds import SuccessEmbed
from .bios_group import bios_group

logger = logging.getLogger(__name__)


@bios_group.command()
async def delete(inter: discord.Interaction) -> None:
    """
    Delete all of your personal info stored in Sandpiper.
    """
    db = await piper(inter).components.user_data.get_database()
    await db.delete_user(inter.user.id)
    await SuccessEmbed("Deleted all of your personal info!").send(inter)
