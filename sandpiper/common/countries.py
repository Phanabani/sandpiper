__all__ = [
    "DEFAULT_FLAG",
    "Country",
    "colloquial_country_names",
    "timezone_to_country_code",
    "get_country_flag_emoji_from_timezone",
    "fuzzy_match_country",
]

from typing import Protocol, cast, get_args

import pycountry
import pytz

from sandpiper.common.time import TimezoneType

DEFAULT_FLAG = ":flag_white:"


class Country(Protocol):
    alpha_2: str
    alpha_3: str
    # This attr won't be `None` -- it won't exist, but I have no way of
    # annotating that properly
    common_name: str | None
    flag: str
    name: str
    numeric: str
    # May not exist
    official_name: str | None


colloquial_country_names = {
    "britain": "United Kingdom",
    "england": "United Kingdom",
    "north ireland": "United Kingdom",
    "uk": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    #
    "us": "United States",
    "usa": "United States",
}

timezone_to_country_code = {
    tz: country_code
    for country_code, timezones in pytz.country_timezones.items()
    for tz in timezones
}


def get_country_flag_emoji_from_timezone(tz: str | TimezoneType) -> str:
    if isinstance(tz, get_args(TimezoneType)):
        tz: str = tz.zone
    elif not isinstance(tz, str):
        raise TypeError(f"tz must be a str or pytz timezone, got {type(tz)}")

    code = timezone_to_country_code.get(tz)
    country = cast(Country, pycountry.countries.get(alpha_2=code))
    if country is None:
        return DEFAULT_FLAG
    return country.flag


def fuzzy_match_country(name: str) -> list[Country]:
    name = colloquial_country_names.get(name.lower(), name)
    try:
        return cast(list[Country], pycountry.countries.search_fuzzy(name))
    except LookupError:
        return []
