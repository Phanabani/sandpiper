__all__ = [
    "MagicMock_",
    "isinstance_mock_supported",
    "patch_all_symbol_imports",
]

import sys
from typing import Any, Optional
from unittest import mock

import pytest


class MagicMock_(mock.MagicMock):
    """
    Identical to MagicMock, but the ``name`` kwarg will be parsed as a regular
    kwarg (assigned to the mock as an attribute).
    """

    def __init__(self, *args, _name_: Optional[str] = None, **kwargs):
        if _name_ is None:
            _name_ = ""
        name_attr = kwargs.pop("name", None)
        super().__init__(*args, name=_name_, **kwargs)
        self.name = name_attr


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


def patch_all_symbol_imports(
    target_symbol: Any,
    match_prefix: Optional[str] = None,
    skip_substring: Optional[str] = None,
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
        name_matches = match_prefix is None or module.__name__.startswith(match_prefix)
        should_skip = skip_substring is not None and skip_substring in module.__name__
        if not name_matches or should_skip:
            continue

        # Iterate through this module's locals
        # Again, make a copy
        for local_name, local in list(module.__dict__.items()):
            if local is target_symbol:
                # Patch this symbol local to the module
                patchers.append(
                    mock.patch(f"{module.__name__}.{local_name}", autospec=True)
                )

    return patchers
