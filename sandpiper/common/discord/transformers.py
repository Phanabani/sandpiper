from __future__ import annotations

__all__ = ["CountryTransformer", "DateTransformer", "TimezoneTransformer"]

from datetime import date
import logging
from typing import cast

from discord import Interaction
from discord.app_commands import Choice, Transformer
import pycountry
import pytz
from pytz.exceptions import UnknownTimeZoneError

from sandpiper.common.countries import Country, fuzzy_match_country
from sandpiper.common.discord import MAX_AUTOCOMPLETE_CHOICES
from sandpiper.common.exceptions import UserError
from sandpiper.common.time import TimezoneType, fuzzy_match_timezone, parse_date

logger = logging.getLogger(__name__)


class CountryTransformer(Transformer):
    MAX_MATCHES = MAX_AUTOCOMPLETE_CHOICES

    async def autocomplete(
        self, interaction: Interaction, value: int | float | str, /
    ) -> list[Choice[str]]:
        if len(value) < 2:
            return []

        if country_matches := fuzzy_match_country(value):
            return [
                Choice(name=country.name, value=country.alpha_2)
                for country in country_matches
            ][: self.MAX_MATCHES]
        return []

    async def transform(
        self, interaction: Interaction, country_alpha_2: str
    ) -> Country:
        try:
            return cast(Country, pycountry.countries.get(alpha_2=country_alpha_2))
        except LookupError:
            raise UserError(f'Country "{country_alpha_2}" does not exist')


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


class TimezoneTransformer(Transformer):
    MAX_MATCHES = 8
    BEST_MATCH_THRESHOLD = 75
    LOWER_SCORE_CUTOFF = 75

    async def autocomplete(
        self, interaction: Interaction, value: int | float | str, /
    ) -> list[Choice[str]]:
        if len(value) < 3:
            return []

        if tz_matches := fuzzy_match_timezone(
            value,
            best_match_threshold=self.BEST_MATCH_THRESHOLD,
            lower_score_cutoff=self.LOWER_SCORE_CUTOFF,
            limit=self.MAX_MATCHES,
        ):
            return [Choice(name=tz[0], value=tz[0]) for tz in tz_matches.matches]
        return []

    async def transform(self, interaction: Interaction, tz_name: str) -> TimezoneType:
        try:
            return pytz.timezone(tz_name)
        except UnknownTimeZoneError:
            raise UserError(f'Timezone "{tz_name}" does not exist')
