from operator import setitem
from pathlib import Path
from typing import Callable, NoReturn, Union

from sandpiper.common.time import TimezoneType

__all__ = (
    "DEFAULT_FLAG",
    "country_code_to_country_name",
    "timezone_to_country_code",
    "to_regional_indicator",
    "get_country_flag_emoji",
    "get_country_flag_emoji_from_timezone",
)

DEFAULT_FLAG = ":flag_white:"


def _parse_db_file(file_name, per_line: Callable[[dict, list[str]], NoReturn]) -> dict:
    file = Path(__file__).parent / file_name
    if not file.exists():
        raise FileNotFoundError(f"Can't find IANA database file {file}")

    out = {}
    with file.open("rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            per_line(out, line.strip("\n").split("\t"))

    return out


country_code_to_country_name: dict[str, str] = _parse_db_file(
    "iso3166.tab", lambda d, fields: setitem(d, fields[0], fields[1])
)
timezone_to_country_code: dict[str, str] = _parse_db_file(
    "zone.tab", lambda d, fields: setitem(d, fields[2], fields[0])
)


def to_regional_indicator(char: str) -> str:
    code = ord(char)
    if code < 65 or code > 90:
        raise ValueError(f"char must be a single char from A-Z")
    return chr(code + 127397)


def get_country_flag_emoji(country_id: str) -> str:
    if len(country_id) != 2:
        raise ValueError(f"country_id must be a 2-character string")
    return "".join(to_regional_indicator(i) for i in country_id)


def get_country_flag_emoji_from_timezone(tz: Union[str, TimezoneType]):
    if isinstance(tz, TimezoneType.__args__):
        tz: str = tz.zone
    elif not isinstance(tz, str):
        raise TypeError(f"tz must be a str or pytz timezone, got {type(tz)}")

    code = timezone_to_country_code.get(tz)
    return get_country_flag_emoji(code) if code is not None else DEFAULT_FLAG
