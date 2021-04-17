import datetime as dt
from typing import *
import unittest

from sandpiper.common.time import parse_time


class TestParseTime(unittest.TestCase):

    def assert_time(
            self, timestr: str, time: Optional[dt.time], tz: Optional[str]
    ):
        if time is None:
            if tz is not None:
                raise ValueError("Can't test for only timezone without time")
            with self.assertRaises(ValueError):
                parse_time(timestr)
            return

        time_parsed, tz_parsed = parse_time(timestr)
        self.assertEqual(time_parsed, time)
        if tz is not None:
            self.assertEqual(tz_parsed, tz)
        else:
            self.assertIsNone(tz_parsed)

    def test_hour(self):
        self.assert_time(
            '5', dt.time(5, 0), None
        )
        self.assert_time(
            '13', dt.time(13, 0), None
        )
        # Not a real time
        self.assert_time(
            '24', None, None
        )
        self.assert_time(
            '5am', dt.time(5, 0), None
        )
        self.assert_time(
            '5 AM', dt.time(5, 0), None
        )
        self.assert_time(
            '5pm', dt.time(17, 0), None
        )
        self.assert_time(
            '5 PM', dt.time(17, 0), None
        )

    def test_colon(self):
        self.assert_time(
            '5:30', dt.time(5, 30), None
        )
        self.assert_time(
            '05:30', dt.time(5, 30), None
        )
        # Not real times
        self.assert_time(
            '24:00', None, None
        )
        self.assert_time(
            '1:60', None, None
        )
        self.assert_time(
            '5:30am', dt.time(5, 30), None
        )
        self.assert_time(
            '5:30 AM', dt.time(5, 30), None
        )
        self.assert_time(
            '5:30pm', dt.time(17, 30), None
        )
        self.assert_time(
            '5:30 PM', dt.time(17, 30), None
        )

    def test_no_colon(self):
        self.assert_time(
            '05', dt.time(5, 0), None
        )
        # Not real times
        self.assert_time(
            '53', None, None
        )
        self.assert_time(
            '2400', None, None
        )
        self.assert_time(
            '160', None, None
        )
        self.assert_time(
            '530', dt.time(5, 30), None
        )
        self.assert_time(
            '0530', dt.time(5, 30), None
        )
        self.assert_time(
            '0530am', dt.time(5, 30), None
        )
        self.assert_time(
            '530am', dt.time(5, 30), None
        )
        self.assert_time(
            '530 AM', dt.time(5, 30), None
        )
        self.assert_time(
            '530pm', dt.time(17, 30), None
        )
        self.assert_time(
            '530 PM', dt.time(17, 30), None
        )

    def test_hour_timezone(self):
        # This is ambiguous with a unit definition
        self.assert_time(
            '5 new york', None, None
        )
        self.assert_time(
            '5am new york', dt.time(5, 0), 'new york'
        )
        self.assert_time(
            '5 AM new york', dt.time(5, 0), 'new york'
        )
        self.assert_time(
            '5pm new york', dt.time(17, 0), 'new york'
        )
        self.assert_time(
            '5 PM new york', dt.time(17, 0), 'new york'
        )

    def test_colon_timezone(self):
        self.assert_time(
            '5:30 new york', dt.time(5, 30), 'new york'
        )
        self.assert_time(
            '5:30am new york', dt.time(5, 30), 'new york'
        )
        self.assert_time(
            '5:30 AM new york', dt.time(5, 30), 'new york'
        )
        self.assert_time(
            '5:30pm new york', dt.time(17, 30), 'new york'
        )
        self.assert_time(
            '5:30 PM new york', dt.time(17, 30), 'new york'
        )

    def test_no_colon_timezone(self):
        # These two are ambiguous with a unit definition
        self.assert_time(
            '530 new york', None, None
        )
        self.assert_time(
            '0530 new york', None, None
        )
        self.assert_time(
            '530am new york', dt.time(5, 30), 'new york'
        )
        self.assert_time(
            '530 AM new york', dt.time(5, 30), 'new york'
        )
        self.assert_time(
            '530pm new york', dt.time(17, 30), 'new york'
        )
        self.assert_time(
            '530 PM new york', dt.time(17, 30), 'new york'
        )
