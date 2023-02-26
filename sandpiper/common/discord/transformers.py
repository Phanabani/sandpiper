from __future__ import annotations

__all__ = ["DateTransformer", "TimezoneTransformer"]

from datetime import date
import logging

from discord import Interaction
from discord.app_commands import Choice, Transformer
import pytz
from pytz.exceptions import UnknownTimeZoneError

from sandpiper.common.exceptions import UserError
from sandpiper.common.time import TimezoneType, fuzzy_match_timezone, parse_date

logger = logging.getLogger(__name__)


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


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class TimezoneTransformer(Transformer):
    MAX_MATCHES = 8
    BEST_MATCH_THRESHOLD = 75
    LOWER_SCORE_CUTOFF = 75

    async def autocomplete(
        self, interaction: Interaction, value: int | float | str, /
    ) -> list[Choice[str]]:
        if len(value) < 3:
            return []

        return self._get_by_tz_name(value)

    async def transform(self, interaction: Interaction, tz_name: str) -> TimezoneType:
        try:
            return pytz.timezone(tz_name)
        except UnknownTimeZoneError:
            raise UserError(f'Timezone "{tz_name}" does not exist')

    def _get_by_tz_name(self, value: int | float | str) -> list[Choice[str]]:
        if tz_matches := fuzzy_match_timezone(
            value,
            best_match_threshold=self.BEST_MATCH_THRESHOLD,
            lower_score_cutoff=self.LOWER_SCORE_CUTOFF,
            limit=self.MAX_MATCHES,
        ):
            return [Choice(name=tz[0], value=tz[0]) for tz in tz_matches.matches]
        return []
