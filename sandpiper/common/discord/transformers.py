from __future__ import annotations

__all__ = ["DateTransformer"]

from datetime import date

from discord import Interaction
from discord.app_commands import Transformer

from sandpiper.common.discord.misc import logger
from sandpiper.common.exceptions import UserError
from sandpiper.common.time import parse_date


# noinspection PyAbstractClass,PyMethodMayBeStatic,PyUnusedLocal
class DateTransformer(Transformer):
    async def transform(self, interaction: Interaction, date_str: str) -> date:
        try:
            return parse_date(date_str)
        except ValueError as e:
            logger.info(f"Failed to parse date (str={date_str!r} reason={e})")
            raise UserError(
                "Bad date format. Try something like this: `1997-08-27`, "
                "`31 Oct`, `June 15 2001`"
            )
