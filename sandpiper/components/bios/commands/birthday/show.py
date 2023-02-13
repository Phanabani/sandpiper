__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from sandpiper.common.time import format_date
from sandpiper.components.bios.strings import user_info_str
from .birthday_group import birthday_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@birthday_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Display your birthday
    """
    user_id, db = await get_id_and_db(inter)

    birthday = await db.get_birthday(user_id)
    birthday = format_date(birthday)
    privacy = await db.get_privacy_birthday(user_id)
    await InfoEmbed(user_info_str("Birthday", birthday, privacy)).send(inter)
