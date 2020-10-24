from typing import Union

import pytz

__all__ = ['TimezoneType']

TimezoneType = Union[pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo]
