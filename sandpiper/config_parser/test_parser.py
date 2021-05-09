from typing import Any, Literal, Union

import pytest

from .exceptions import *
from .parser import ConfigCompound


def assert_type_value(value, assert_type: type, assert_value):
    __tracebackhide__ = True
    assert isinstance(value, assert_type)
    assert value == assert_value


class TestSimple:

    def test_none(self):
        class C(ConfigCompound):
            field: None
        parsed = C('{"field": null}')
        assert parsed.field is None
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_bool(self):
        class C(ConfigCompound):
            field: bool
        parsed = C('{"field": true}')
        assert parsed.field is True
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_int(self):
        class C(ConfigCompound):
            field: int
        parsed = C('{"field": 1}')

        assert_type_value(parsed.field, int, 1)
        with pytest.raises(TypeError):
            parsed = C('{"field": "hi"}')

    def test_float(self):
        class C(ConfigCompound):
            field: float
        parsed = C('{"field": 1.0}')
        assert_type_value(parsed.field, float, 1.0)
        with pytest.raises(TypeError):
            parsed = C('{"field": "hi"}')

    def test_str(self):
        class C(ConfigCompound):
            field: str
        parsed = C('{"field": "hi"}')
        assert_type_value(parsed.field, str, 'hi')
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_invalid(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: bytes

    def test_multi(self):
        class C(ConfigCompound):
            fieldA: int
            fieldB: str

        parsed = C('{"fieldA": 1, "fieldB": "hi"}')
        assert_type_value(parsed.fieldA, int, 1)
        assert_type_value(parsed.fieldB, str, 'hi')


class TestSpecialTyping:

    def test_any(self):
        class C(ConfigCompound):
            field: Any

        parsed = C('{"field": true}')
        assert parsed.field is True

        parsed = C('{"field": 1}')
        assert_type_value(parsed.field, int, 1)

        parsed = C('{"field": "hi"}')
        assert_type_value(parsed.field, str, 'hi')

    def test_union(self):
        class C(ConfigCompound):
            field: Union[int, str]

    def test_union_err(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[int, bytes]

    def test_union_nested(self):
        class C(ConfigCompound):
            field: Union[bool, Union[int, Union[float, str]]]

    def test_union_nested_err(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: Union[bool, Union[int, Union[float, bytes]]]

    def test_tuple(self):
        class C(ConfigCompound):
            field: tuple

    def test_tuple_args(self):
        class C(ConfigCompound):
            field: tuple[bool, int, str]

    def test_list(self):
        class C(ConfigCompound):
            field: list

    def test_list_args(self):
        class C(ConfigCompound):
            field: list[int]

    def test_literal(self):
        class C(ConfigCompound):
            field: Literal[5]

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        with pytest.raises(ValueError):
            C('{"field": 4}')

    def test_literal_multi(self):
        class C(ConfigCompound):
            field: Literal[5, 4]

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        parsed = C('{"field": 4}')
        assert_type_value(parsed.field, int, 4)

        with pytest.raises(ValueError):
            C('{"field": 3}')
