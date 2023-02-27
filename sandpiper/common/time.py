__all__ = [
    "TimezoneType",
    "no_zeropad",
    "time_format",
    "parse_time",
    "parse_date",
    "format_date",
    "utc_now",
    "localize_time_to_datetime",
    "day_of_the_year",
    "sort_dates_no_year",
    "TimezoneMatches",
    "fuzzy_match_timezone",
]

from dataclasses import dataclass
import datetime as dt
import re
from typing import Optional, Union, cast

import pytz
from thefuzz import fuzz, process as fuzzy_process
import tzlocal

TimezoneType = Union[pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo]

time_pattern = re.compile(
    r"""
    ^
    (?P<hour>[0-2]?\d)
    (?::?(?P<minute>\d{2}))?
    \s*
    (?:(?P<period_am>a|am)|(?P<period_pm>p|pm))?
    $
    """,
    re.I | re.X,
)

time_pattern_with_timezone = re.compile(
    r"""
    ^
    (?:
        (?P<hour>[0-2]?\d)
        (?:
            (?P<colon>:)?
            (?P<minute>\d{2})
        )?
        (?:\ ?(?P<period>
            (?P<period_am>a|am)
            |(?P<period_pm>p|pm)
        ))?
        |(?P<keyword>
            (?P<now>now)
            |(?P<noon>noon)
            |(?P<midnight>midnight)
        )
    )
    (?(period)
        \ (?P<timezone1>\S.*)
        |(?(colon)
            \ (?P<timezone2>\S.*)
            |(?(keyword)
                \ (?P<timezone_keyword>\S.*)
            )
        )
    )?
    $
    """,
    re.I | re.X,
)

date_pattern_simple = re.compile(
    r"""
    ^(?P<year>\d{4})
    [/-](?P<month>\d\d)
    [/-](?P<day>\d\d)$
    """,
    re.X,
)

date_pattern_words = re.compile(
    r"""
    ^(?:(?P<day1>\d{1,2})\ )?
    (?P<month>
        jan(?:uary)?
        |feb(?:ruary)?
        |mar(?:ch)?
        |apr(?:il)?
        |may
        |june?
        |july?
        |aug(?:ust)?
        |sep(?:t(?:ember)?)?
        |oct(?:ober)?
        |nov(?:ember)?
        |dec(?:ember)?
    )
    (?:\ (?P<day2>\d{1,2}))?
    (?:\ (?P<year>\d{4}))?$
    """,
    re.I | re.X,
)

months = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

try:
    # Unix strip zero-padding
    no_zeropad = "-"
    dt.datetime.now().strftime(f"%{no_zeropad}d")
except ValueError:
    try:
        # Windows strip zero-padding
        no_zeropad = "#"
        dt.datetime.now().strftime(f"%{no_zeropad}d")
    except ValueError:
        # Fallback without stripping zero-padding
        no_zeropad = ""

time_format = f"%{no_zeropad}I:%M %p (%H:%M)"


def utc_now() -> dt.datetime:
    # Get the system-local timezone and use it to localize dt.datetime.now()
    local_tz = cast(TimezoneType, tzlocal.get_localzone())
    return local_tz.localize(dt.datetime.now())


def parse_time(time_str: str) -> tuple[dt.time, Optional[str], bool]:
    """
    Parse a string as a time specifier of the general format "12:34 PM".
    Can optionally include a timezone name.

    :return: A tuple of (time, timezone_name, definitely_time), where
        ``definitely_time`` is a bool representing whether you can be certain
        the string is a time (a colon or AM/PM was matched, or a keyword was
        used). This is helpful for meaningful error feedback.
    """

    match = time_pattern_with_timezone.match(time_str)
    if not match:
        raise ValueError("No match")

    # Handle keyword times
    if match["keyword"]:
        if match["now"]:
            now = utc_now()
            # This is a little heavy-handed because instead of just passing
            # back the localized datetime, we're passing the time and the
            # timezone name which will then be fuzzily matched elsewhere...
            # but it's the simplest way for now since this method doesn't
            # handle the timezone parsing. Maybe it could change in the future.
            return now.time(), cast(TimezoneType, now.tzinfo).zone, True

        if match["midnight"]:
            time = dt.time(0, 0)
        elif match["noon"]:
            time = dt.time(12, 0)
        else:
            raise ValueError("This should be impossible but let's be safe")
        return time, match["timezone_keyword"] or None, True

    hour = int(match["hour"])
    minute = int(match["minute"] or 0)

    if (0 > hour > 23) or (0 > minute > 59):
        raise ValueError("Hour or minute is out of range")

    if match["period_pm"]:
        if hour < 12:
            # This is PM and we use 24 hour times in datetime, so add 12 hours
            hour += 12
        elif hour == 12:
            # 12 PM is 12:00
            pass
        else:
            raise ValueError("24 hour times do not use AM or PM")
    elif match["period_am"]:
        if hour < 12:
            # AM, so no change
            pass
        elif hour == 12:
            # 12 AM is 00:00
            hour = 0
        else:
            raise ValueError("24 hour times do not use AM or PM")

    return (
        dt.time(hour, minute),
        match["timezone1"] or match["timezone2"] or None,
        bool(match["colon"] or match["period"]),
    )


def parse_date(date_str: str) -> dt.date:
    if match := date_pattern_simple.match(date_str):
        year = int(match["year"])
        month = int(match["month"])
        day = int(match["day"])

    elif match := date_pattern_words.match(date_str):
        year = int(match["year"] or 1)
        month = months[match["month"][:3].lower()]
        day1 = match["day1"]
        day2 = match["day2"]
        if (day1 is None) == (day2 is None):
            raise ValueError("You must specify the day")
        day = int(day1 if day1 is not None else day2)

    else:
        raise ValueError("No match")

    return dt.date(year, month, day)


def format_date(date: Optional[dt.date]):
    if date is None:
        return None
    if date.year == 1:
        return date.strftime(f"%B %{no_zeropad}d")
    return date.strftime("%Y-%m-%d")


def localize_time_to_datetime(time: dt.time, basis_tz: TimezoneType) -> dt.datetime:
    """
    Turn a time into a datetime, localized in the given timezone based on the
    current day in that timezone.

    :param time: the time in `basis_tz`'s current day
    :param basis_tz: the timezone for localizing the datetime. It is also used
        to determine the datetime's date.
    :returns: An aware datetime where the date is the current day in `basis_tz`
        and the time is equal to `time`.
    """

    # Convert UTC now to the basis timezone
    now_basis = utc_now().astimezone(basis_tz)

    # Create the datetime we think the user is trying to specify by using
    # their current local day and adding the hour and minute arguments.
    # Return the localized datetime
    basis_time = dt.datetime(
        now_basis.year, now_basis.month, now_basis.day, time.hour, time.minute
    )
    return basis_tz.localize(basis_time)


def day_of_the_year(datetime: Union[dt.date, dt.datetime]):
    return int(datetime.strftime("%j"))


def _sort_dates_no_year_func(d: dt.date, now: dt.datetime):
    d_int = day_of_the_year(d.replace(year=1))
    now_int = day_of_the_year(now.replace(year=1))
    if now_int > d_int:
        d_int += 367
    return d_int


def sort_dates_no_year(dates: list, key=lambda x: x, now: Optional[dt.datetime] = None):
    if now is None:
        now = utc_now()
    return sorted(dates, key=lambda x: _sort_dates_no_year_func(key(x), now))


@dataclass
class TimezoneMatches:
    matches: list[tuple[str, int]] = None
    best_match: Optional[TimezoneType] = False
    has_multiple_best_matches: bool = False


def fuzzy_match_timezone(
    tz_str: str, best_match_threshold=75, lower_score_cutoff=50, limit=5
) -> TimezoneMatches:
    """
    Fuzzily match a timezone based on given timezone name.

    :param tz_str: timezone name to fuzzily match in pytz's list of timezones
    :param best_match_threshold: Score from 0-100 that the highest scoring
        match must be greater than to qualify as the best match
    :param lower_score_cutoff: Lower score limit from 0-100 to qualify matches
        for storage in ``TimezoneMatches.matches``
    :param limit: Maximum number of matches to store in
        ``TimezoneMatches.matches``
    """

    # I think partial_token_sort_ratio provides the best experience.
    # The regular token_sort_ratio just feels weird because it doesn't support
    # substrings. Searching "Amst" would pick "GMT" rather than "Amsterdam".
    # The _set_ratio methods are totally unusable.
    matches: list[tuple[str, int]] = fuzzy_process.extractBests(
        tz_str,
        pytz.common_timezones,
        scorer=fuzz.partial_token_sort_ratio,
        score_cutoff=lower_score_cutoff,
        limit=limit,
    )
    tz_matches = TimezoneMatches(matches)

    if matches and matches[0][1] >= best_match_threshold:
        # Best match
        tz_matches.best_match = pytz.timezone(matches[0][0])
        if len(matches) > 1 and matches[1][1] == matches[0][1]:
            # There are multiple best matches
            # I think given our inputs and scoring algorithm, this shouldn't
            # ever happen, but I'm leaving it just in case
            tz_matches.has_multiple_best_matches = True
    return tz_matches
