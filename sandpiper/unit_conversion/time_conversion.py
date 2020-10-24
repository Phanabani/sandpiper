import datetime as dt
import logging
import re
from typing import List, Tuple

import discord

from ..common.time import *
from ..user_info import UserData

__all__ = ['time_format', 'UserTimezoneUnset', 'convert_time_to_user_timezones']

logger = logging.getLogger('sandpiper.conversion.time_conversion')

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


class UserTimezoneUnset(Exception):
    pass


class TimeParsingError(Exception):
    pass


def parse_time(string: str, basis_tz: TimezoneType) -> dt.datetime:
    """
    Parse a string as a time specifier of the general format "12:34 PM".

    :raises: TimeParsingError if parsing failed in an expected way
    """

    # Convert UTC now to the basis timezone
    now_basis = utc_now().astimezone(basis_tz)

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

    # Create the datetime we think the user is trying to specify by using
    # their current local day and adding the hour and minute arguments.
    # Return the localized datetime
    basis_time = dt.datetime(now_basis.year, now_basis.month, now_basis.day,
                             hour, minute)
    return basis_tz.localize(basis_time)


def convert_time_to_user_timezones(
        user_data: UserData, user_id: int, guild: discord.Guild,
        time_strs: List[str]
) -> Tuple[List[Tuple[str, List[dt.datetime]]], List[str]]:
    """
    Convert times.

    :param user_data: the UserData cog for interacting with the database
    :param user_id: the id of the user asking for a time conversion
    :param guild: the guild the conversion is occurring in
    :param time_strs: a list of strings that may be time specifiers
    :returns: A tuple of (conversions, failed).
        ``failed`` is a list of strings that could not be converted.
        ``conversions`` is a list of tuples of (tz_name, converted_times).
        ``tz_name`` is the name of the timezone the following times are in.
        ``converted_times`` is a list of datetimes localized to every timezone
        occupied by users in the guild.
    """

    db = user_data.get_database()
    basis_tz = db.get_timezone(user_id)
    if basis_tz is None:
        raise UserTimezoneUnset()
    user_timezones = [tz for user_id, tz in db.get_all_timezones()
                      if guild.get_member(user_id)]

    parsed_times = []
    failed = []
    for tstr in time_strs:
        try:
            parsed_times.append(parse_time(tstr, basis_tz))
        except TimeParsingError as e:
            logger.debug(f"Failed to parse time string (string={tstr}, "
                         f"reason={e})")
            failed.append(tstr)
        except:
            logger.warning(f"Unhandled exception while parsing time string "
                           f"(string={tstr})", exc_info=True)

    if not parsed_times:
        return [], failed

    conversions = []
    for tz in user_timezones:
        tz_name: str = tz.zone
        times = [time.astimezone(tz) for time in parsed_times]
        conversions.append((tz_name, times))
    conversions.sort(key=lambda conv: conv[1][0].utcoffset())

    return conversions, failed
