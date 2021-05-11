from typing import Annotated as A

import pytest

from .exceptions import *
from .parser import *
from .transformers import *


def assert_type_value(value, assert_type: type, assert_value):
    __tracebackhide__ = True
    assert isinstance(value, assert_type)
    assert value == assert_value


class TestAnnotations:

    def test_fromtype_implicit_to(self):
        class C(ConfigCompound):
            field: A[str, FromType(int)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123")

        with pytest.raises(TypeError):
            C('{"field": "123"}')

    def test_fromtype_multiple_implicit_to_type_err(self):
        with pytest.raises(ConfigSchemaError, match='implicit'):
            class C(ConfigCompound):
                field: A[str, FromType(int), FromType(str)]

    def test_fromtype_explicit_to(self):
        class C(ConfigCompound):
            field: A[str, FromType(int, str)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123")

    def test_fromtype_explicit_to_chained(self):
        class C(ConfigCompound):
            field: A[str, FromType(int, float), FromType(float, str)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123.0")

    def test_fromtype_explicit_to_type_mismatch(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: A[str, FromType(int, float)]

    def test_fromtype_implicit_with_bounded_after(self):
        # I want the shorthand implicit notation available if it's used at
        # the last FromType, however I think it's difficult to understand
        # what's going on if more transformers come after it
        with pytest.raises(ConfigSchemaError):
            class C(ConfigCompound):
                field: A[int, FromType(str), Bounded(2, 4)]

    def test_fromtype_explicit_with_bounded_after(self):
        class C(ConfigCompound):
            field: A[int, FromType(str, int), Bounded(2, 4)]

        parsed = C('{"field": "3"}')
        assert_type_value(parsed.field, int, 3)

        with pytest.raises(ValueError):
            parsed = C('{"field": "5"}')

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
