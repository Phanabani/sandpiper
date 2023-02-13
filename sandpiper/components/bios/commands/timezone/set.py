__all__ = ["set"]

import logging

import discord
from discord.app_commands import Transform

from sandpiper.common.discord import TimezoneTransformer
from sandpiper.common.embeds import SuccessEmbed
from sandpiper.common.time import TimezoneType
from sandpiper.components.bios.strings import PrivacyExplanation
from sandpiper.components.user_data import PrivacyType
from .timezone_group import timezone_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@timezone_group.command()
async def set(
    inter: discord.Interaction,
    new_timezone: Transform[TimezoneType, TimezoneTransformer],
) -> None:
    """
    Set your timezone (usually your nearest major city)
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_timezone(user_id, new_timezone)
    embed = SuccessEmbed(f"Timezone set to **{new_timezone}**!")
    if await db.get_privacy_timezone(user_id) == PrivacyType.PRIVATE:
        embed.append("\n" + PrivacyExplanation.get("timezone"))

    await embed.send(inter)
