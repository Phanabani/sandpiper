from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, cast

import discord
from discord import InteractionResponse

from sandpiper.common.discord import cheap_user_hash
from sandpiper.common.logging import warn_component_none
from sandpiper.common.time import sort_dates_no_year, utc_now
from sandpiper.components.birthdays.commands.birthdays import birthdays_group
from sandpiper.components.user_data import PrivacyType

if TYPE_CHECKING:
    from sandpiper import Sandpiper

    # noinspection PyUnresolvedReferences
    from sandpiper.components.birthdays import Birthdays

PAST_BIRTHDAY_EMOJIS = "🔷"
UPCOMING_BIRTHDAY_EMOJIS = "🎂🍰🧁🎈🎁🎉🎊"

logger = logging.getLogger(__name__)


async def format_bday_upcoming(
    sandpiper: Sandpiper, user_id: int, guild: discord.Guild, past: bool
) -> Optional[str]:
    db = await sandpiper.components.user_data.get_database()

    user = sandpiper.get_user(user_id)
    if user is None:
        return None
    if not guild.get_member(user_id):
        return None
    if await db.get_privacy_birthday(user_id) is not PrivacyType.PUBLIC:
        return None

    emojis_set = PAST_BIRTHDAY_EMOJIS if past else UPCOMING_BIRTHDAY_EMOJIS
    emoji = emojis_set[cheap_user_hash(user_id) % len(emojis_set)]

    bday = await db.get_birthday(user_id)
    user_qual = f"{user.name}#{user.discriminator}"

    if await db.get_privacy_preferred_name(user_id) is PrivacyType.PUBLIC:
        name = f"**{await db.get_preferred_name(user_id)}** ({user_qual})"
    else:
        name = f"**{user_qual}**"

    return f"{emoji}  `{bday:%b %d}` - {name}"


@birthdays_group.command(description="View upcoming birthdays")
async def upcoming(inter: discord.Interaction) -> None:
    sandpiper = cast("Sandpiper", inter.client)
    if (birthdays := sandpiper.components.birthdays) is None:
        return warn_component_none(logger, "Birthdays")
    birthdays = cast("Birthdays", birthdays)
    response = cast(InteractionResponse, inter.response)

    past_raw, upcoming_raw = await birthdays.get_past_upcoming_birthdays(
        birthdays.past_birthdays_day_range, birthdays.upcoming_birthdays_day_range
    )
    now = utc_now()

    past = []
    for user_id, _ in sort_dates_no_year(past_raw, lambda x: x[1], now):
        bday_str = await format_bday_upcoming(
            sandpiper, user_id, inter.guild, past=True
        )
        if bday_str:
            past.append(bday_str)

    upcoming = []
    for user_id, _ in sort_dates_no_year(upcoming_raw, lambda x: x[1], now):
        bday_str = await format_bday_upcoming(
            sandpiper, user_id, inter.guild, past=False
        )
        if bday_str:
            upcoming.append(bday_str)

    if not past and not upcoming:
        return await response.send_message("No birthdays yet!")

    msg = []
    if past:
        msg.append("Past birthdays:")
        msg.extend(past)

    if past and upcoming:
        msg.append("")

    if upcoming:
        msg.append(f"Upcoming birthdays:")
        msg.extend(upcoming)

    await response.send_message("\n".join(msg))
