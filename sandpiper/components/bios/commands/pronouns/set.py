__all__ = ["set"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from sandpiper.common.exceptions import UserError
from sandpiper.components.bios.strings import PrivacyExplanation
from sandpiper.components.user_data import PrivacyType
from .pronouns_group import pronouns_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@pronouns_group.command()
async def set(inter: discord.Interaction, new_pronouns: str) -> None:
    """
    Set your pronouns (must be 64 characters or less)
    """
    if len(new_pronouns) > 64:
        raise UserError(
            f"Pronouns must be 64 characters or less (yours: " f"{len(new_pronouns)})."
        )

    user_id, db = await get_id_and_db(inter)

    await db.set_pronouns(user_id, new_pronouns)
    embed = SuccessEmbed("Pronouns set!", join="\n\n")

    if await db.get_privacy_pronouns(user_id) == PrivacyType.PRIVATE:
        embed.append(PrivacyExplanation.get("pronouns"))

    await embed.send(inter)
