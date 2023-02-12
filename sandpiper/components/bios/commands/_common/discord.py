__all__ = ["get_id_and_db"]

import discord

from sandpiper.common.discord import piper
from sandpiper.components.user_data import Database


async def get_id_and_db(inter: discord.Interaction) -> tuple[int, Database]:
    return inter.user.id, await piper(inter).components.user_data.get_database()
