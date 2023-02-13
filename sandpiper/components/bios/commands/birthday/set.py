__all__ = ["set"]

import datetime as dt
import logging

import discord
from discord.app_commands import Transform

from sandpiper.common.discord import DateTransformer
from sandpiper.common.embeds import SuccessEmbed
from sandpiper.components.bios.strings import BirthdayExplanations
from sandpiper.components.user_data import PrivacyType
from .birthday_group import birthday_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@birthday_group.command()
async def set(
    inter: discord.Interaction, new_birthday: Transform[dt.datetime, DateTransformer]
) -> None:
    """
    Set your birthday. Birth year is optional. (e.g. "Aug 27 1997", "27 August", "1997-08-27")
    """
    user_id, db = await get_id_and_db(inter)

    await db.set_birthday(user_id, new_birthday)

    embed = SuccessEmbed("Birthday set!", join="\n\n")

    # Tell them how their privacy affects their birthday announcement
    bday_privacy = await db.get_privacy_birthday(user_id)
    if bday_privacy is PrivacyType.PRIVATE:
        embed.append(BirthdayExplanations.birthday_is_private_soft_suggest)

    elif bday_privacy is PrivacyType.PUBLIC:
        embed.append(BirthdayExplanations.birthday_is_public)

        age_privacy = await db.get_privacy_age(user_id)
        if age_privacy is PrivacyType.PRIVATE:
            embed.append(BirthdayExplanations.age_is_private)
        if age_privacy is PrivacyType.PUBLIC:
            embed.append(BirthdayExplanations.age_is_public)

    await embed.send(inter)
