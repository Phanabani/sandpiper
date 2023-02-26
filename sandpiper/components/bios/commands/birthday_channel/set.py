__all__ = ["set"]

import logging

import discord

from sandpiper.common.embeds import SuccessEmbed
from .birthday_channel_group import birthday_channel_group
from .._common.discord import get_id_and_db

logger = logging.getLogger(__name__)


@birthday_channel_group.command()
async def set(inter: discord.Interaction, new_channel: discord.TextChannel) -> None:
    """
    Set the birthday notification channel (where Sandpiper will send birthday
    messages)
    """
    __, db = await get_id_and_db(inter)

    await db.set_guild_birthday_channel(inter.guild.id, new_channel.id)
    await SuccessEmbed("Birthday channel set!").send(inter)
