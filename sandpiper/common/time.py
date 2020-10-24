import datetime as dt
from typing import Union, cast

import pytz

__all__ = ['TimezoneType', 'utc_now']

import tzlocal

TimezoneType = Union[pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo]


def utc_now() -> dt.datetime:
    # Get the system-local timezone and use it to localize dt.datetime.now()
    local_tz = cast(TimezoneType, tzlocal.get_localzone())
    return local_tz.localize(dt.datetime.now())
