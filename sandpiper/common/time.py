import datetime as dt
import re
from typing import Optional, Union, cast

import pytz
import tzlocal

__all__ = [
    'TimezoneType', 'time_format', 'parse_time', 'parse_date', 'format_date',
    'utc_now', 'localize_time_to_datetime'
]

TimezoneType = Union[pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo]

time_pattern = re.compile(
    r'^(?P<hour>[0-2]?\d)'
    r'(?::(?P<minute>\d{2}))?'
    r'\s*'
    r'(?:(?P<period_am>a|am)|(?P<period_pm>p|pm))?$',
    re.I
)

date_pattern_simple = re.compile(
    r'^(?P<year>\d{4})'
    r'[/-](?P<month>\d\d)'
    r'[/-](?P<day>\d\d)$'
)

date_pattern_words = re.compile(
    r'^(?:(?P<day1>\d{1,2}) )?'
    r'(?P<month>'
        r'(?:jan(?:uary)?)'
        r'|(?:feb(?:ruary)?)'
        r'|(?:mar(?:ch)?)'
        r'|(?:apr(?:il)?)'
        r'|(?:may)'
        r'|(?:june?)'
        r'|(?:july?)'
        r'|(?:aug(?:ust)?)'
        r'|(?:sep(?:t(?:ember)?)?)'
        r'|(?:oct(?:ober)?)'
        r'|(?:nov(?:ember)?)'
        r'|(?:dec(?:ember)?)'
    r')'
    r'(?: (?P<day2>\d{1,2}))?'
    r'(?: (?P<year>\d{4}))?$',
    re.I
)

months = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

try:
    # Unix strip zero-padding
    no_zeropad = '-'
    dt.datetime.now().strftime(f'%{no_zeropad}d')
except ValueError:
    try:
        # Windows strip zero-padding
        no_zeropad = '#'
        dt.datetime.now().strftime(f'%{no_zeropad}d')
    except ValueError:
        # Fallback without stripping zero-padding
        no_zeropad = ''

time_format = f'%{no_zeropad}I:%M %p (%H:%M)'


def utc_now() -> dt.datetime:
    # Get the system-local timezone and use it to localize dt.datetime.now()
    local_tz = cast(TimezoneType, tzlocal.get_localzone())
    return local_tz.localize(dt.datetime.now())


def parse_time(time_str: str) -> dt.time:
    """
    Parse a string as a time specifier of the general format "12:34 PM".
    """

    match = time_pattern.match(time_str)
    if not match:
        raise ValueError('No match')

    hour = int(match.group('hour'))
    minute = int(match.group('minute') or 0)

    if (0 > hour > 23) or (0 > minute > 59):
        raise ValueError('Hour or minute is out of range')

    if match.group('period_pm'):
        if hour < 12:
            # This is PM and we use 24 hour times in datetime, so add 12 hours
            hour += 12
        elif hour == 12:
            # 12 PM is 12:00
            pass
        else:
            raise ValueError('24 hour times do not use AM or PM')
    elif match.group('period_am'):
        if hour < 12:
            # AM, so no change
            pass
        elif hour == 12:
            # 12 AM is 00:00
            hour = 0
        else:
            raise ValueError('24 hour times do not use AM or PM')

    return dt.time(hour, minute)


def parse_date(date_str: str) -> dt.date:
    if match := date_pattern_simple.match(date_str):
        year = int(match.group('year'))
        month = int(match.group('month'))
        day = int(match.group('day'))

    elif match := date_pattern_words.match(date_str):
        year = int(match.group('year') or 1)
        month = months[match.group('month')[:3].lower()]
        day1 = match.group('day1')
        day2 = match.group('day2')
        if (day1 is None) == (day2 is None):
            raise ValueError("You must specify the day")
        day = int(day1 if day1 is not None else day2)

    else:
        raise ValueError('No match')

    return dt.date(year, month, day)


def format_date(date: Optional[dt.date]):
    if date is None:
        return None
    if date.year == 1:
        return date.strftime(f'%B %{no_zeropad}d')
    return date.strftime('%Y-%m-%d')


def localize_time_to_datetime(time: dt.time,
                              basis_tz: TimezoneType) -> dt.datetime:
    """
    Turn a time into a datetime, localized in the given timezone based on the
    current day in that timezone.

    :param time: the time in `basis_tz`'s current day
    :param basis_tz: the timezone for localizing the datetime. It is also used
        to determine the datetime's date.
    :returns: An aware timezone where the date is the current day in `basis_tz`
        and the time is equal to `time`.
    """

    # Convert UTC now to the basis timezone
    now_basis = utc_now().astimezone(basis_tz)

    # Create the datetime we think the user is trying to specify by using
    # their current local day and adding the hour and minute arguments.
    # Return the localized datetime
    basis_time = dt.datetime(now_basis.year, now_basis.month, now_basis.day,
                             time.hour, time.minute)
    return basis_tz.localize(basis_time)
