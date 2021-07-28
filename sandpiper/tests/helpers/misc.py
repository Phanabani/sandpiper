from collections import Counter
from collections.abc import Iterable
import re
from typing import NoReturn, TypeVar, Union

__all__ = [
    'assert_in', 'assert_regex',
    'assert_one_if_list',
    'assert_count_equal'
]

V = TypeVar('V')


def assert_in(str_: str, *substrings: str) -> NoReturn:
    """
    Dispatch ``msg`` to the bot and assert that it replies with one
    message and contains each substring in ``substrings``.
    """
    __tracebackhide__ = True
    for substr in substrings:
        assert substr in str_


def assert_regex(str_: str, *patterns: str) -> NoReturn:
    """
    Dispatch ``msg`` to the bot and assert that it replies with one
    message and matches each regex pattern in ``patterns``.
    """
    __tracebackhide__ = True
    for pattern in patterns:
        assert re.search(pattern, str_), (
            f'Pattern "{pattern}" did not match any part of "{str_}"'
        )


def assert_one_if_list(x: Union[list[V], V]) -> V:
    """
    Assert, if `x` is a list, that x has only one element and return that
    element, else return `x` as is.
    """
    __tracebackhide__ = True
    if isinstance(x, list):
        assert len(x) == 1, f"Expected only one item in list, got {len(x)}"
        return x[0]
    return x


def assert_count_equal(it_a: Iterable, it_b: Iterable) -> NoReturn:
    """
    Assert that both iterables have the same elements, regardless of order.
    Inspired by unittest.TestCase.assertCountEqual.
    """
    count_a = Counter(it_a)
    count_b = Counter(it_b)
    assert count_a == count_b
