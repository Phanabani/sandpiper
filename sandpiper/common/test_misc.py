import pytest

from sandpiper.common.misc import listify


class TestListify:

    def test_zero(self):
        values = []
        assert listify(values) == ''

    def test_one(self):
        values = ['a']
        assert listify(values) == 'a'

    def test_two(self):
        values = list('ab')
        assert listify(values) == 'a and b'

    def test_three(self):
        values = list('abc')
        assert listify(values) == 'a, b, and c'

    def test_five(self):
        values = list('abcde')
        assert listify(values) == 'a, b, c, d, and e'

    def test_five_trim_three(self):
        values = list('abcde')
        assert listify(values, 3) == 'a, b, c, and 2 others'
