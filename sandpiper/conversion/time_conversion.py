import datetime as dt
import logging
from typing import List, Set, Tuple

import discord

from ..common.time import *
from ..user_info import UserData

__all__ = ['UserTimezoneUnset', 'convert_time_to_user_timezones']

logger = logging.getLogger('sandpiper.conversion.time_conversion')


class UserTimezoneUnset(Exception):
    pass


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
    # Filter out repeat timezones and timezones of users outside this guild
    all_timezones = db.get_all_timezones()
    logger.debug(f"All timezones: {all_timezones}")
    user_timezones: Set[TimezoneType] = {tz for user_id, tz in all_timezones
                                         if guild.get_member(user_id)}
    logger.debug(f"Filtered timezones: {user_timezones}")

    # Attempt to parse the strings as times and populate success and failure
    # lists accordingly
    parsed_times = []
    failed = []
    for tstr in time_strs:
        try:
            parsed_times.append(parse_time(tstr, basis_tz))
        except TimeParsingError as e:
            logger.info(f"Failed to parse time string (string={tstr}, "
                        f"reason={e})")
            failed.append(tstr)
        except:
            logger.warning(f"Unhandled exception while parsing time string "
                           f"(string={tstr})", exc_info=True)

    if not parsed_times:
        return [], failed

    # Iterate over each timezone and convert all times to that timezone
    conversions = []
    for tz in user_timezones:
        tz_name: str = tz.zone
        times = [time.astimezone(tz) for time in parsed_times]
        conversions.append((tz_name, times))
    conversions.sort(key=lambda conv: conv[1][0].utcoffset())

    return conversions, failed
