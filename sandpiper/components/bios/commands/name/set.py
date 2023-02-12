__all__ = ["set"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from sandpiper.common.exceptions import UserError
from sandpiper.components.bios.strings import PrivacyExplanation
from sandpiper.components.user_data import PrivacyType
from .name_group import name_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@name_group.command()
async def set(inter: discord.Interaction, new_name: str) -> None:
    """
    Set your preferred name (must be 64 characters or less)
    """
    if len(new_name) > 64:
        raise UserError(f"Name must be 64 characters or less (yours: {len(new_name)}).")

    user_id, db = await get_id_and_db(inter)

    await db.set_preferred_name(user_id, new_name)
    embed = SuccessEmbed("Preferred name set!", join="\n\n")

    if await db.get_privacy_preferred_name(user_id) is PrivacyType.PRIVATE:
        embed.append(PrivacyExplanation.get("name"))

    await embed.send(inter)
