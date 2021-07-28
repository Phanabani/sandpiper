from collections import Counter
from collections.abc import Iterable
import re
import sys
from typing import Any, NoReturn, Optional, TypeVar, Union
from unittest import mock

__all__ = [
    'assert_in', 'assert_regex',
    'assert_one_if_list',
    'assert_count_equal',
    'patch_all_symbol_imports',
    'isinstance_mock_supported'
]

import pytest

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


def patch_all_symbol_imports(
        target_symbol: Any, match_prefix: Optional[str] = None,
        skip_substring: Optional[str] = None
):
    """
    Iterate through every visible module (in sys.modules) that starts with
    `match_prefix` to find imports of `target_symbol` and return a list
    of patchers for each import.

    This is helpful when you want to patch a module, function, or object
    everywhere in your project's code, even when it is imported with an alias.

    Example:

    ::

        import datetime

        # Setup
        patchers = patch_all_symbol_imports(datetime, 'my_project.', 'test')
        for patcher in patchers:
            mock_dt = patcher.start()
            # Do stuff with the mock

        # Teardown
        for patcher in patchers:
            patcher.stop()

    :param target_symbol: the symbol to search for imports of (may be a module,
        a function, or some other object)
    :param match_prefix: if not None, only search for imports in
        modules that begin with this string
    :param skip_substring: if not None, skip any module that contains this
        substring (e.g. 'test' to skip unit test modules)
    :return: a list of patchers for each import of the target symbol
    """

    patchers = []

    # Iterate through all currently imported modules
    # Make a copy in case it changes
    for module in list(sys.modules.values()):
        name_matches = (
                match_prefix is None
                or module.__name__.startswith(match_prefix)
        )
        should_skip = (
            skip_substring is not None and skip_substring in module.__name__
        )
        if not name_matches or should_skip:
            continue

        # Iterate through this module's locals
        # Again, make a copy
        for local_name, local in list(module.__dict__.items()):
            if local is target_symbol:
                # Patch this symbol local to the module
                patchers.append(mock.patch(
                    f'{module.__name__}.{local_name}', autospec=True
                ))

    return patchers


def isinstance_mock_supported(__obj, __class_or_tuple):
    if isinstance(__class_or_tuple, mock.Mock):
        try:
            return isinstance(__obj, __class_or_tuple._mock_wraps)
        except AttributeError:
            pytest.fail(
                "Mock object needs to use the wrap parameter so the original "
                "type can be accessed for isinstance testing"
            )
    return isinstance(__obj, __class_or_tuple)
