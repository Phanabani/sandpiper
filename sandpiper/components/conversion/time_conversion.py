__all__ = ["UserTimezoneUnset", "TimezoneNotFound", "convert_time_to_user_timezones"]

from collections import defaultdict
from collections.abc import Iterable
import datetime as dt
import logging
from typing import Optional, Union, cast

import discord

from sandpiper.common.misc import RuntimeMessages
from sandpiper.common.time import *
from sandpiper.components.user_data import Database

logger = logging.getLogger("sandpiper.conversion.time_conversion")

T_ConvertedTimes = list[tuple[str, list[dt.datetime]]]
T_ConvertedTimesGroupedUnderInputTimezones = list[
    tuple[Optional[str], T_ConvertedTimes]
]


class UserTimezoneUnset(Exception):
    def __str__(self):
        return (
            "Your timezone is not set. Use the `help timezone set` command "
            "for more info."
        )


class TimezoneNotFound(Exception):
    def __init__(self, timezone: str):
        self.timezone = timezone

    def __str__(self):
        return f'Timezone "{self.timezone}" not found'


def _get_timezone(name: str) -> Optional[TimezoneType]:
    """
    Get the timezone that best matches this name. May return None if the fuzzy
    search score is less than 50.
    """
    matches = fuzzy_match_timezone(name, best_match_threshold=50, limit=1)
    return matches.best_match or None


async def _get_guild_timezones(db: Database, guild: discord.Guild) -> set[TimezoneType]:
    """
    Get all user timezones from the given guild.

    :param db: the Database to get user data from
    :param guild: the guild to limit the search to
    :return: a set of user timezones in this guild
    """
    all_timezones = await db.get_all_timezones()
    return {
        # Filter out timezones of users outside this guild
        tz
        for user_id, tz in all_timezones
        if guild.get_member(user_id)
    }


async def _convert_times(
    times: list[dt.datetime], out_timezones: Union[TimezoneType, Iterable[TimezoneType]]
) -> T_ConvertedTimes:
    """
    Convert a list of datetimes to the given timezones.

    :param times: a list of timezone-aware datetimes to convert
    :param out_timezones: one or more timezones to convert each datetime to
    :return: a list of tuples of (timezone_name, converted_times), where
        ``converted_times`` is a list of datetimes converted to that timezone
    """
    if isinstance(out_timezones, TimezoneType.__args__):
        out_timezones = (out_timezones,)

    conversions: T_ConvertedTimes = []
    for tz in out_timezones:
        times = [time.astimezone(tz) for time in times]
        conversions.append((tz.zone, times))
    conversions.sort(key=lambda conv: conv[1][0].utcoffset())
    return conversions


async def convert_time_to_user_timezones(
    db: Database,
    user_id: int,
    guild: discord.Guild,
    time_strs: list[tuple[str, str]],
    *,
    runtime_msgs: RuntimeMessages,
) -> tuple[T_ConvertedTimesGroupedUnderInputTimezones, list[tuple[str, str]]]:
    """
    Convert times.

    :param db: the Database adapter for getting user timezones
    :param user_id: the id of the user asking for a time conversion
    :param guild: the guild the conversion is occurring in
    :param time_strs: a list of tuples of (time, timezone) where ``time`` is a
        string that may be a time and ``timezone`` is an optional timezone
        name
    :param runtime_msgs: A collection of messages that were generated during
        runtime. These may be reported back to the user.
    :returns: A tuple of (conversions, failed, exceptions).
        ``failed`` is a list of tuples of (quantity, unit) that could not be converted.
        ``conversions`` is a list of tuples of (tz_name, converted_times).
        ``tz_name`` is the name of the timezone the following times are in.
        ``converted_times`` is a list of datetimes localized to every timezone
            occupied by users in the guild.
    """

    # region Parse input

    # Attempt to parse the strings as times and populate success and failure
    # lists accordingly

    # This dict is a mapping of timezone keys to datetimes
    # Each datetime under a given timezone will be converted to that timezone
    # only. The None key is a special case, where each datetime mapped to it
    # will be converted to all user timezones in the database
    out_timezone_map: dict[Optional[TimezoneType], list[dt.datetime]] = defaultdict(
        list
    )
    failed: list[tuple[str, str]] = []  # Strings that should pass on to unit conversion
    user_tz = None
    for tstr, timezone_out_str in time_strs:
        try:
            parsed_time, timezone_in_str, definitely_time = parse_time(tstr)
        except ValueError as e:
            logger.info(f"Failed to parse time string (string={tstr!r}, reason={e})")
            # Failed to parse as a time, so pass it on to unit conversion
            failed.append((tstr, timezone_out_str))
            continue
        except:
            logger.warning(
                f"Unhandled exception while parsing time string " f"(string={tstr!r})",
                exc_info=True,
            )
            continue

        if timezone_in_str is not None:
            # User supplied a source timezone
            timezone_in = _get_timezone(timezone_in_str)
            if timezone_in is None:
                # If we matched timezone_in, we already know tstr is definitely
                # a time
                runtime_msgs += TimezoneNotFound(timezone_in_str)
                continue
        else:
            # Use the user's timezone
            if user_tz is None:
                # Only get this once
                user_tz = await db.get_timezone(user_id)
                if user_tz is None:
                    runtime_msgs.add_type_once(UserTimezoneUnset())
            timezone_in = user_tz

        if timezone_out_str:
            # Parse the output timezone specified by the user
            timezone_out = _get_timezone(timezone_out_str)
            if timezone_out is None:
                if definitely_time:
                    # We know this is a time, so this unfound timezone should
                    # be reported and not passed on to unit conversion
                    runtime_msgs += TimezoneNotFound(timezone_out_str)
                else:
                    # This might be a unit
                    failed.append((tstr, timezone_out_str))
        else:
            timezone_out = None

        local_dt = localize_time_to_datetime(parsed_time, timezone_in)
        out_timezone_map[timezone_out].append(local_dt)

    if not out_timezone_map:
        return [], failed

    # endregion
    # region Do conversions

    conversions: T_ConvertedTimesGroupedUnderInputTimezones = []

    if out_timezone_map[None]:
        # No specific output timezone, so use all the timezones in the guild
        converted = await _convert_times(
            out_timezone_map[None], await _get_guild_timezones(db, guild)
        )
        if len(out_timezone_map) == 1:
            # If there aren't any other out timezones, don't print the timezone
            # name header
            conversions.append((None, converted))
        else:
            # Otherwise, print this header to distinguish it from the others
            conversions.append(("All timezones", converted))

    # Handle any other output timezones
    for timezone_out, times in out_timezone_map.items():
        if timezone_out is None:
            # We already did this first
            continue
        if not times:
            continue
        converted = await _convert_times(times, timezone_out)
        conversions.append((cast(TimezoneType, times[0].tzinfo).zone, converted))

    return conversions, failed

    # endregion
