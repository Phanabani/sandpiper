from contextlib import contextmanager
from typing import Type, Union

import pytest

from .parser import ConfigCompound
from .exceptions import *


@contextmanager
def not_raises(expected_exc: Type[Exception]):
    try:
        yield
    except expected_exc as e:
        pytest.fail(f"Exception {type(e)} raised when it should explicitly not")
    except Exception as e:
        pytest.fail(f"Unexpected exception: {type(e)}")


class TestSimple:

    def test_none(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: None

    def test_bool(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: bool

    def test_int(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: int

    def test_float(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: float

    def test_str(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: str

    def test_invalid(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: bytes


class TestSpecialTyping:

    def test_union(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[int, str]

    def test_union_err(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[int, bytes]

    def test_union_nested(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[bool, Union[int, Union[float, str]]]

    def test_union_nested_err(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[bool, Union[int, Union[float, bytes]]]

    def test_tuple(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: tuple

    def test_tuple_args(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: tuple[bool, int, str]

    def test_list(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: list

    def test_list_args(self):
        with not_raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: list[int]
