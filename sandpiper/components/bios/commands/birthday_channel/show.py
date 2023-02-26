__all__ = ["show"]

import logging

import discord

from sandpiper.common.embeds import InfoEmbed
from sandpiper.components.bios.strings import info_str
from .birthday_channel_group import birthday_channel_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@birthday_channel_group.command()
async def show(inter: discord.Interaction) -> None:
    """
    Show the birthday notification channel (where Sandpiper will send birthday
    messages)
    """
    __, db = await get_id_and_db(inter)

    bday_channel_id = await db.get_guild_birthday_channel(inter.guild.id)
    if bday_channel_id is None:
        await InfoEmbed(info_str("Birthday channel", "N/A")).send(inter)
        return

    await InfoEmbed(
        info_str("Birthday channel", f"<#{bday_channel_id}> (id={bday_channel_id})")
    ).send(inter)
