from .pronouns import *


class TestOneClass:

    def test_one_case(self):
        pronouns = Pronouns.parse('He')
        assert pronouns == [
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_two_cases(self):
        pronouns = Pronouns.parse('She/her')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself')
        ]

    def test_three_cases(self):
        pronouns = Pronouns.parse('They/them/their')
        assert pronouns == [
            Pronouns('they', 'them', 'their', 'theirs', 'themself')
        ]

    def test_five_cases(self):
        pronouns = Pronouns.parse('Xe/xem/xyr/xyrs/xemself')
        assert pronouns == [
            Pronouns('xe', 'xem', 'xyr', 'xyrs', 'xemself')
        ]


class TestTwoClasses:

    def test_one_case(self):
        pronouns = Pronouns.parse('They/he')
        assert pronouns == [
            Pronouns('they', 'them', 'their', 'theirs', 'themself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_two_cases(self):
        pronouns = Pronouns.parse('She/her he/him')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]


class TestUniqueClass:

    def test_one_case(self):
        pronouns = Pronouns.parse('Pup')
        assert pronouns == [
            Pronouns('pup', 'pup', 'pups', 'pups', 'pupself')
        ]

    def test_three_cases(self):
        pronouns = Pronouns.parse('Unique/missing/some')
        assert pronouns == [
            Pronouns('unique', 'missing', 'some', 'uniques', 'uniqueself')
        ]

    def test_five_cases(self):
        pronouns = Pronouns.parse('Unique/but/not/missing/any')
        assert pronouns == [
            Pronouns('unique', 'but', 'not', 'missing', 'any')
        ]


class TestMisc:

    def test_no_args(self):
        pronouns = Pronouns.parse('')
        assert pronouns == [
            Pronouns('they', 'them', 'their', 'theirs', 'themself')
        ]

    def test_backslash(self):
        pronouns = Pronouns.parse('she\\he')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_spaces(self):
        pronouns = Pronouns.parse('she / he')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_repeats(self):
        pronouns = Pronouns.parse('She/her he/him she/her')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]
