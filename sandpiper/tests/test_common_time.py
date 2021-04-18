import datetime as dt
from typing import *
import unittest
import unittest.mock as mock

import pytz

from sandpiper.common.time import parse_time


class TestParseTime(unittest.TestCase):

    STATIC_NOW = dt.datetime(2020, 6, 1, 9, 32)

    def setUp(self):
        self.patch_time()

    def patch_time(self):
        # Patch datetime to use a static datetime
        patcher = mock.patch('sandpiper.common.time.dt', autospec=True)
        mock_datetime = patcher.start()
        self.addCleanup(patcher.stop)

        mock_datetime.datetime.now.return_value = self.STATIC_NOW
        mock_datetime.datetime.side_effect = (
            lambda *a, **kw: dt.datetime(*a, **kw)
        )
        mock_datetime.date.side_effect = (
            lambda *a, **kw: dt.date(*a, **kw)
        )
        mock_datetime.time.side_effect = (
            lambda *a, **kw: dt.time(*a, **kw)
        )

        # Patch localzone to use UTC
        patcher = mock.patch(
            'sandpiper.common.time.tzlocal.get_localzone', autospec=True
        )
        mock_localzone = patcher.start()
        self.addCleanup(patcher.stop)

        mock_localzone.return_value = pytz.UTC

    def assert_time(
            self, timestr: str, time: Optional[dt.time], tz: Optional[str],
            definitely_time: Optional[bool]
    ):
        __tracebackhide__ = True
        if time is None:
            if tz is not None:
                raise ValueError("Can't test for only timezone without time")
            with self.assertRaises(ValueError):
                parse_time(timestr)
            return

        time_parsed, tz_parsed, definitely_time_parsed = parse_time(timestr)
        assert time_parsed == time

        if tz is not None:
            assert tz_parsed == tz
        else:
            assert tz_parsed is None

        if definitely_time is not None:
            assert definitely_time_parsed is definitely_time

    def test_hour(self):
        self.assert_time(
            '5', dt.time(5, 0), None, False
        )
        self.assert_time(
            '13', dt.time(13, 0), None, False
        )
        self.assert_time(
            '5am', dt.time(5, 0), None, True
        )
        self.assert_time(
            '5 AM', dt.time(5, 0), None, True
        )
        self.assert_time(
            '5pm', dt.time(17, 0), None, True
        )
        self.assert_time(
            '5 PM', dt.time(17, 0), None, True
        )

    def test_hour_invalid_times(self):
        self.assert_time(
            '24', None, None, False
        )

    def test_colon(self):
        self.assert_time(
            '5:30', dt.time(5, 30), None, True
        )
        self.assert_time(
            '05:30', dt.time(5, 30), None, True
        )
        self.assert_time(
            '5:30am', dt.time(5, 30), None, True
        )
        self.assert_time(
            '5:30 AM', dt.time(5, 30), None, True
        )
        self.assert_time(
            '5:30pm', dt.time(17, 30), None, True
        )
        self.assert_time(
            '5:30 PM', dt.time(17, 30), None, True
        )

    def test_colon_not_real_times(self):
        self.assert_time(
            '24:00', None, None, None
        )
        self.assert_time(
            '1:60', None, None, None
        )

    def test_no_colon(self):
        self.assert_time(
            '05', dt.time(5, 0), None, False
        )
        self.assert_time(
            '530', dt.time(5, 30), None, False
        )
        self.assert_time(
            '0530', dt.time(5, 30), None, False
        )
        self.assert_time(
            '0530am', dt.time(5, 30), None, True
        )
        self.assert_time(
            '530am', dt.time(5, 30), None, True
        )
        self.assert_time(
            '530 AM', dt.time(5, 30), None, True
        )
        self.assert_time(
            '530pm', dt.time(17, 30), None, True
        )
        self.assert_time(
            '530 PM', dt.time(17, 30), None, True
        )

    def test_no_colon_invalid_times(self):
        self.assert_time(
            '53', None, None, None
        )
        self.assert_time(
            '2400', None, None, None
        )
        self.assert_time(
            '160', None, None, None
        )

    def test_hour_timezone(self):
        self.assert_time(
            '5am new york', dt.time(5, 0), 'new york', True
        )
        self.assert_time(
            '5 AM new york', dt.time(5, 0), 'new york', True
        )
        self.assert_time(
            '5pm new york', dt.time(17, 0), 'new york', True
        )
        self.assert_time(
            '5 PM new york', dt.time(17, 0), 'new york', True
        )

    def test_hour_timezone_ambiguous(self):
        # This is ambiguous with a unit definition
        self.assert_time(
            '5 new york', None, None, None
        )

    def test_colon_timezone(self):
        self.assert_time(
            '5:30 new york', dt.time(5, 30), 'new york', True
        )
        self.assert_time(
            '5:30am new york', dt.time(5, 30), 'new york', True
        )
        self.assert_time(
            '5:30 AM new york', dt.time(5, 30), 'new york', True
        )
        self.assert_time(
            '5:30pm new york', dt.time(17, 30), 'new york', True
        )
        self.assert_time(
            '5:30 PM new york', dt.time(17, 30), 'new york', True
        )

    def test_no_colon_timezone(self):
        self.assert_time(
            '530am new york', dt.time(5, 30), 'new york', True
        )
        self.assert_time(
            '530 AM new york', dt.time(5, 30), 'new york', True
        )
        self.assert_time(
            '530pm new york', dt.time(17, 30), 'new york', True
        )
        self.assert_time(
            '530 PM new york', dt.time(17, 30), 'new york', True
        )

    def test_no_colon_timezone_ambiguous(self):
        # Ambiguous with a unit definition
        self.assert_time(
            '530 new york', None, None, None
        )
        self.assert_time(
            '0530 new york', None, None, None
        )

    def test_random_string(self):
        self.assert_time('hello', None, None, None)

    def test_keywords_basic(self):
        self.assert_time('now', self.STATIC_NOW.time(), 'UTC', True)
        self.assert_time('noon', dt.time(12, 0), None, True)
        self.assert_time('midnight', dt.time(0, 0), None, True)

    def test_keywords_with_am(self):
        self.assert_time('now am', self.STATIC_NOW.time(), 'UTC', True)
        self.assert_time('noon am', dt.time(12, 0), 'am', True)
        self.assert_time('midnight am', dt.time(0, 0), 'am', True)

    def test_keywords_timezone(self):
        self.assert_time('now new york', self.STATIC_NOW.time(), 'UTC', True)
        self.assert_time('noon new york', dt.time(12, 0), 'new york', True)
        self.assert_time('midnight new york', dt.time(0, 0), 'new york', True)
