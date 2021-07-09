from .pronouns import *


class TestParse:

    # region One class

    def test_one_class_one_case(self):
        pronouns = Pronouns.parse('He')
        assert pronouns == [
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_one_class_two_cases(self):
        pronouns = Pronouns.parse('She/her')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself')
        ]

    def test_one_class_three_cases(self):
        pronouns = Pronouns.parse('They/them/their')
        assert pronouns == [
            Pronouns('they', 'them', 'their', 'theirs', 'themself')
        ]

    def test_one_class_five_cases(self):
        pronouns = Pronouns.parse('Xe/xem/xyr/xyrs/xemself')
        assert pronouns == [
            Pronouns('xe', 'xem', 'xyr', 'xyrs', 'xemself')
        ]

    # endregion
    # region Two classes

    def test_two_classes_one_case(self):
        pronouns = Pronouns.parse('They/he')
        assert pronouns == [
            Pronouns('they', 'them', 'their', 'theirs', 'themself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_two_classes_two_cases(self):
        pronouns = Pronouns.parse('She/her he/him')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    # endregion
    # region Unique class

    def test_unique_class_one_case(self):
        pronouns = Pronouns.parse('Pup')
        assert pronouns == [
            Pronouns('pup', 'pup', 'pups', 'pups', 'pupself')
        ]

    def test_unique_class_three_cases(self):
        pronouns = Pronouns.parse('Unique/missing/some')
        assert pronouns == [
            Pronouns('unique', 'missing', 'some', 'uniques', 'uniqueself')
        ]

    def test_unique_class_five_cases(self):
        pronouns = Pronouns.parse('Unique/but/not/missing/any')
        assert pronouns == [
            Pronouns('unique', 'but', 'not', 'missing', 'any')
        ]

    # endregion
    # region Other

    def test_backslash(self):
        pronouns = Pronouns.parse('he\\him')
        assert pronouns == [
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    def test_repeats(self):
        pronouns = Pronouns.parse('She/her he/him she/her')
        assert pronouns == [
            Pronouns('she', 'her', 'her', 'hers', 'herself'),
            Pronouns('he', 'him', 'his', 'his', 'himself')
        ]

    # endregion
