from __future__ import annotations

__all__ = ["show"]

import logging

import discord

from sandpiper.common.discord import piper
from sandpiper.common.embeds import InfoEmbed
from sandpiper.common.time import format_date
from sandpiper.components.bios.commands.bios import bios_group
from sandpiper.components.bios.strings import user_info_str

logger = logging.getLogger(__name__)


@bios_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display all of your personal info stored in Sandpiper.
    """
    db = await piper(inter).components.user_data.get_database()
    user_id = inter.user.id

    preferred_name = await db.get_preferred_name(user_id)
    pronouns = await db.get_pronouns(user_id)
    birthday = await db.get_birthday(user_id)
    birthday = format_date(birthday)
    age = await db.get_age(user_id)
    age = age if age is not None else "N/A"
    timezone = await db.get_timezone(user_id)

    p_preferred_name = await db.get_privacy_preferred_name(user_id)
    p_pronouns = await db.get_privacy_pronouns(user_id)
    p_birthday = await db.get_privacy_birthday(user_id)
    p_age = await db.get_privacy_age(user_id)
    p_timezone = await db.get_privacy_timezone(user_id)

    await InfoEmbed(
        [
            user_info_str("Name", preferred_name, p_preferred_name),
            user_info_str("Pronouns", pronouns, p_pronouns),
            user_info_str("Birthday", birthday, p_birthday),
            user_info_str("Age", age, p_age),
            user_info_str("Timezone", timezone, p_timezone),
        ]
    ).send(inter)
