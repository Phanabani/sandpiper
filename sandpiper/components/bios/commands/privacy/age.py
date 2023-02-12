__all__ = ["age"]

import logging

import discord

from sandpiper.common.discord import piper
from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.bios.strings import BirthdayExplanations
from sandpiper.components.user_data import PrivacyType
from .privacy_group import privacy_group

logger = logging.getLogger(__name__)


@privacy_group.command()
async def age(inter: discord.Interaction, new_privacy: PrivacyType) -> None:
    """
    Set the privacy of your age to either 'private' or 'public'
    """
    user_id = inter.user.id
    db = await piper(inter).components.user_data.get_database()
    await db.set_privacy_age(user_id, new_privacy)
    embed = SuccessEmbed("Age privacy set!", join="\n\n")

    # Tell them how their privacy affects their birthday announcement
    bday_privacy = await db.get_privacy_birthday(user_id)
    if bday_privacy is PrivacyType.PUBLIC:
        if new_privacy is PrivacyType.PRIVATE:
            embed.append(BirthdayExplanations.age_is_private)
        if new_privacy is PrivacyType.PUBLIC:
            embed.append(BirthdayExplanations.age_is_public)

    await embed.send(inter)
