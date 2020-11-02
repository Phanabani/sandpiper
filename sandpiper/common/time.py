import datetime as dt
import re
from typing import Union, cast

import pytz
import tzlocal

__all__ = ['TimezoneType', 'TimeParsingError', 'time_format', 'parse_time',
           'utc_now', 'localize_time_to_datetime']

TimezoneType = Union[pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo]

time_pattern = re.compile(
    r'^(?P<hour>[0-2]?\d)'
    r'(?::(?P<minute>\d{2}))?'
    r'\s*'
    r'(?:(?P<period_am>a|am)|(?P<period_pm>p|pm))?$',
    re.I
)

try:
    # Unix strip zero-padding
    time_format = '%-I:%M %p (%H:%M)'
    dt.datetime.now().strftime(time_format)
except ValueError:
    try:
        # Windows strip zero-padding
        time_format = '%#I:%M %p (%H:%M)'
        dt.datetime.now().strftime(time_format)
    except ValueError:
        # Fallback without stripping zero-padding
        time_format = '%I:%M %p (%H:%M)'


class TimeParsingError(Exception):
    pass


def utc_now() -> dt.datetime:
    # Get the system-local timezone and use it to localize dt.datetime.now()
    local_tz = cast(TimezoneType, tzlocal.get_localzone())
    return local_tz.localize(dt.datetime.now())


def parse_time(string: str) -> dt.time:
    """
    Parse a string as a time specifier of the general format "12:34 PM".

    :raises TimeParsingError: if parsing failed in an expected way
    """

    match = time_pattern.match(string)
    if not match:
        raise TimeParsingError('No match')

    hour = int(match.group('hour'))
    minute = int(match.group('minute') or 0)

    if (0 > hour > 23) or (0 > minute > 59):
        raise TimeParsingError('Hour or minute is out of range')

    if match.group('period_pm'):
        if hour < 12:
            # This is PM and we use 24 hour times in datetime, so add 12 hours
            hour += 12
        elif hour == 12:
            # 12 PM is 12:00
            pass
        else:
            raise TimeParsingError('24 hour times do not use AM or PM')
    elif match.group('period_am'):
        if hour < 12:
            # AM, so no change
            pass
        elif hour == 12:
            # 12 AM is 00:00
            hour = 0
        else:
            raise TimeParsingError('24 hour times do not use AM or PM')

    return dt.time(hour, minute)


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
