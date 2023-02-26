__all__ = ["notify_birthdays_component"]

from collections.abc import Callable, Coroutine
from functools import wraps
import logging

import discord

from sandpiper.common.discord import piper

logger = logging.getLogger(__name__)


def notify_birthdays_component(
    fn: Callable[[discord.Interaction, ...], Coroutine[object]]
):
    @wraps(fn)
    async def wrapped(inter: discord.Interaction, *args, **kwargs):
        await fn(inter, *args, **kwargs)

        logger.debug(
            f"Notifying birthdays cog about change from command {inter.command.name} "
            f"(user_id={inter.user.id})"
        )
        birthdays = piper(inter).components.birthdays
        await birthdays.notify_change(inter.user.id)

    return wrapped
