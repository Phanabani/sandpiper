from __future__ import annotations
from typing import Annotated as A, Any, Literal, Union

import pytest

from .annotations import *
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

    def test_missing_field(self):
        class C(ConfigCompound):
            fieldA: int
            fieldB: int

        with pytest.raises(MissingFieldError, match='fieldA'):
            C('{"fieldB": 1}')


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


class TestNestedCompounds:

    def test_simple(self):
        class C(ConfigCompound):
            nested: _Nested
            class _Nested(ConfigCompound):
                field: int

        parsed = C('{"nested": {"field": 1}}')
        assert isinstance(parsed.nested, C._Nested)
        assert_type_value(parsed.nested.field, int, 1)

    def test_simple_same_field_names(self):
        class C(ConfigCompound):
            field: str
            nested: _Nested
            class _Nested(ConfigCompound):
                field: int

        parsed = C('{"field": "hi", "nested": {"field": 1}}')
        assert_type_value(parsed.field, str, "hi")
        assert isinstance(parsed.nested, C._Nested)
        assert_type_value(parsed.nested.field, int, 1)


class TestAnnotations:

    def test_fromtype(self):
        class C(ConfigCompound):
            field: A[str, FromType(int)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123")

        with pytest.raises(TypeError):
            C('{"field": "123"}')

    def test_bounded_min(self):
        class C(ConfigCompound):
            field: A[int, Bounded(5, None)]

        with pytest.raises(ValueError):
            C('{"field": 4}')

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        parsed = C('{"field": 6}')
        assert_type_value(parsed.field, int, 6)

    def test_bounded_max(self):
        class C(ConfigCompound):
            field: A[int, Bounded(None, 10)]

        parsed = C('{"field": 9}')
        assert_type_value(parsed.field, int, 9)

        parsed = C('{"field": 10}')
        assert_type_value(parsed.field, int, 10)

        with pytest.raises(ValueError):
            C('{"field": 11}')

    def test_bounded_min_max(self):
        class C(ConfigCompound):
            field: A[int, Bounded(2, 4)]

        with pytest.raises(ValueError):
            C('{"field": 1}')

        parsed = C('{"field": 2}')
        assert_type_value(parsed.field, int, 2)

        parsed = C('{"field": 3}')
        assert_type_value(parsed.field, int, 3)

        parsed = C('{"field": 4}')
        assert_type_value(parsed.field, int, 4)

        with pytest.raises(ValueError):
            C('{"field": 5}')

    def test_bounded_min_equal_to_max(self):
        class C(ConfigCompound):
            field: A[int, Bounded(2, 2)]

        with pytest.raises(ValueError):
            C('{"field": 1}')

        parsed = C('{"field": 2}')
        assert_type_value(parsed.field, int, 2)

        with pytest.raises(ValueError):
            C('{"field": 3}')

    def test_bounded_min_greater_than_max(self):
        with pytest.raises(ValueError):
            class C(ConfigCompound):
                field: A[int, Bounded(2, 1)]


class TestDefaults:

    @staticmethod
    @pytest.fixture
    def simple_compound():
        class C(ConfigCompound):
            intField = 3
            strField = 'hi'
        return C

    def test_empty(self, simple_compound):
        parsed = simple_compound('{}')
        assert_type_value(parsed.intField, int, 3)
        assert_type_value(parsed.strField, str, 'hi')

    def test_missing_one(self, simple_compound):
        parsed = simple_compound('{"intField": 2}')
        assert_type_value(parsed.intField, int, 2)
        assert_type_value(parsed.strField, str, 'hi')

        parsed = simple_compound('{"strField": "hello"}')
        assert_type_value(parsed.intField, int, 3)
        assert_type_value(parsed.strField, str, 'hello')

    def test_bad_type_parsing(self, simple_compound):
        with pytest.raises(TypeError):
            parsed = simple_compound('{"strField": 5}')

    def test_bad_type_definition(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: int = 'hi'

    def test_tuple(self):
        class C(ConfigCompound):
            field = (1, 2, 3)

        parsed = C('{}')
        assert parsed.field == (1, 2, 3)

    def test_list(self):
        class C(ConfigCompound):
            field = [1, 2, 3]

        parsed1 = C('{}')
        assert parsed1.field == [1, 2, 3]

    def test_list_member_inference(self):
        class C(ConfigCompound):
            field = [1, 2, 3]

        parsed = C('{"field": [3, 4, 5]}')
        assert parsed.field == [3, 4, 5]

        with pytest.raises(TypeError):
            parsed = C('{"field": ["hi", "there"]}')

    def test_list_identity(self):
        class C(ConfigCompound):
            field = [1, 2, 3]

        parsed1 = C('{}')
        parsed2 = C('{}')
        assert parsed1.field == [1, 2, 3]
        assert parsed2.field == [1, 2, 3]
        assert parsed2.field is not parsed1.field