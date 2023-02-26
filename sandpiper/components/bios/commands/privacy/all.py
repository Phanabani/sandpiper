__all__ = ["all"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.bios.strings import BirthdayExplanations
from sandpiper.components.user_data import PrivacyType
from .privacy_group import privacy_group
from .._common.discord import get_id_and_db
from .._common.notify_birthdays_component import notify_birthdays_component

logger = logging.getLogger(__name__)


@privacy_group.command()
@notify_birthdays_component
async def all(inter: discord.Interaction, new_privacy: PrivacyType) -> None:
    """
    Set the privacy of all of your personal info at once to either 'private' or
    'public'
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_privacy_preferred_name(user_id, new_privacy)
    await db.set_privacy_pronouns(user_id, new_privacy)
    await db.set_privacy_birthday(user_id, new_privacy)
    await db.set_privacy_age(user_id, new_privacy)
    await db.set_privacy_timezone(user_id, new_privacy)

    embed = SuccessEmbed("All privacies set!", join="\n\n")
    if new_privacy is PrivacyType.PUBLIC:
        embed.append(BirthdayExplanations.birthday_is_public)
        embed.append(BirthdayExplanations.age_is_public)
    elif new_privacy is PrivacyType.PRIVATE:
        embed.append(BirthdayExplanations.birthday_is_private)

    await embed.send(inter)
