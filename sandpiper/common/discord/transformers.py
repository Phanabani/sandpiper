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
from thefuzz import fuzz
from thefuzz.process import extractBests

from sandpiper.common.countries import Country, fuzzy_match_country
from sandpiper.common.discord import MAX_AUTOCOMPLETE_CHOICES
from sandpiper.common.exceptions import UserError
from sandpiper.common.time import TimezoneType, parse_date

logger = logging.getLogger(__name__)


class CountryTransformer(Transformer):
    MAX_MATCHES = MAX_AUTOCOMPLETE_CHOICES

    async def autocomplete(
        self, interaction: Interaction, value: str, /
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
    FUZZY_MAX_MATCHES = 8
    FUZZY_SCORE_CUTOFF = 75

    async def autocomplete(
        self, interaction: Interaction, value: str, /
    ) -> list[Choice[str]]:
        if (country_code := interaction.namespace.country) is not None:
            # NOTE: Discord caches autocomplete results based on each argument
            # value, so if the user enters a country, starts autocompleting
            # timezone, then changes country, the cache won't change. They need
            # to restart the command entering process or type in a new value
            # to set updated results.
            return self._get_tz_by_country(value, country_code)
        # No country supplied, so fuzzy match instead
        return self._try_get_fuzzy_timezone(value)

    async def transform(self, interaction: Interaction, tz_name: str) -> TimezoneType:
        try:
            return pytz.timezone(tz_name)
        except UnknownTimeZoneError:
            raise UserError(f'Timezone "{tz_name}" does not exist')

    @staticmethod
    def _fuzzy_match(
        name: str,
        options: list[str],
        *,
        score_cutoff: int = FUZZY_SCORE_CUTOFF,
        limit: int = FUZZY_MAX_MATCHES,
    ) -> list[Choice[str]]:
        matches = cast(
            list[tuple[str, int]],
            extractBests(
                name,
                options,
                scorer=fuzz.partial_token_sort_ratio,
                score_cutoff=score_cutoff,
                limit=limit,
            ),
        )
        return [Choice(name=i[0], value=i[0]) for i in matches]

    def _get_tz_by_country(self, value: str, country_code: str):
        # This dict lookup could possibly raise KeyError, which is handled
        country_timezones = pytz.country_timezones[country_code]

        if len(value) == 0:
            return [Choice(name=tz, value=tz) for tz in country_timezones][
                :MAX_AUTOCOMPLETE_CHOICES
            ]

        return self._fuzzy_match(
            value, country_timezones, limit=MAX_AUTOCOMPLETE_CHOICES
        )

    def _try_get_fuzzy_timezone(self, value: str) -> list[Choice[str]]:
        if len(value) < 3:
            return []

        return self._fuzzy_match(value, pytz.common_timezones)
