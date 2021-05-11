from __future__ import annotations

from typing import Any, Literal, Union

import pytest

from .exceptions import *
from .parser import ConfigSchema


def assert_type_value(value, assert_type: type, assert_value):
    __tracebackhide__ = True
    assert isinstance(value, assert_type)
    assert value == assert_value


class TestSimple:

    def test_none(self):
        class C(ConfigSchema):
            field: None
        parsed = C('{"field": null}')
        assert parsed.field is None
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_bool(self):
        class C(ConfigSchema):
            field: bool
        parsed = C('{"field": true}')
        assert parsed.field is True
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_int(self):
        class C(ConfigSchema):
            field: int
        parsed = C('{"field": 1}')

        assert_type_value(parsed.field, int, 1)
        with pytest.raises(TypeError):
            parsed = C('{"field": "hi"}')

    def test_float(self):
        class C(ConfigSchema):
            field: float
        parsed = C('{"field": 1.0}')
        assert_type_value(parsed.field, float, 1.0)
        with pytest.raises(TypeError):
            parsed = C('{"field": "hi"}')

    def test_str(self):
        class C(ConfigSchema):
            field: str
        parsed = C('{"field": "hi"}')
        assert_type_value(parsed.field, str, 'hi')
        with pytest.raises(TypeError):
            parsed = C('{"field": 1}')

    def test_invalid(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: bytes

    def test_multi(self):
        class C(ConfigSchema):
            fieldA: int
            fieldB: str

        parsed = C('{"fieldA": 1, "fieldB": "hi"}')
        assert_type_value(parsed.fieldA, int, 1)
        assert_type_value(parsed.fieldB, str, 'hi')

    def test_missing_field(self):
        class C(ConfigSchema):
            fieldA: int
            fieldB: int

        with pytest.raises(MissingFieldError, match='fieldA'):
            C('{"fieldB": 1}')


class TestCollections:

    def test_tuple(self):
        class C(ConfigSchema):
            field: tuple

        parsed = C('{"field": [null, true, "hi"]}')
        assert isinstance(parsed.field, tuple)
        assert parsed.field[0] is None
        assert parsed.field[1] is True
        assert_type_value(parsed.field[2], str, 'hi')

    def test_tuple_args(self):
        class C(ConfigSchema):
            field: tuple[bool, int, str]

        parsed = C('{"field": [true, 1, "hi"]}')
        assert parsed.field[0] is True
        assert_type_value(parsed.field[1], int, 1)
        assert_type_value(parsed.field[2], str, 'hi')

    def test_tuple_args_type_err(self):
        class C(ConfigSchema):
            field: tuple[bool, int, str]

        with pytest.raises(TypeError):
            parsed = C('{"field": [true, true, true]}')

    def test_tuple_args_len_err(self):
        class C(ConfigSchema):
            field: tuple[bool, int, str]

        with pytest.raises(ValueError, match=r'length.+3'):
            parsed = C('{"field": [true, 1, "hi", "extra"]}')

    def test_list(self):
        class C(ConfigSchema):
            field: list

        parsed = C('{"field": [null, true, "hi"]}')
        assert isinstance(parsed.field, list)
        assert parsed.field[0] is None
        assert parsed.field[1] is True
        assert_type_value(parsed.field[2], str, 'hi')

    def test_list_args(self):
        class C(ConfigSchema):
            field: list[int]

        parsed = C('{"field": [1, 2, 3]}')
        assert isinstance(parsed.field, list)
        assert_type_value(parsed.field[0], int, 1)
        assert_type_value(parsed.field[1], int, 2)
        assert_type_value(parsed.field[2], int, 3)

    def test_list_args_type_err(self):
        class C(ConfigSchema):
            field: list[int]

        with pytest.raises(TypeError):
            parsed = C('{"field": [1, 2, false]}')

    def test_dict(self):
        # Assume dict[str, Any]
        class C(ConfigSchema):
            field: dict

        parsed = C('{"field": {"bool": true, "int": 1, "str": "hi"}}')
        assert isinstance(parsed.field, dict)
        assert parsed.field['bool'] is True
        assert_type_value(parsed.field['int'], int, 1)
        assert_type_value(parsed.field['str'], str, 'hi')

    def test_dict_args(self):
        class C(ConfigSchema):
            field: dict[str, int]

        parsed = C('{"field": {"one": 1, "two": 2}}')
        assert isinstance(parsed.field, dict)
        assert_type_value(parsed.field['one'], int, 1)
        assert_type_value(parsed.field['two'], int, 2)

    def test_dict_args_type_err(self):
        class C(ConfigSchema):
            field: dict[str, int]

        with pytest.raises(TypeError):
            parsed = C('{"field": {"one": 1, "two": "two"}}')

    def test_dict_key_not_str(self):
        with pytest.raises(TypeError):
            class C(ConfigSchema):
                field: dict[int, str]


class TestSpecialTyping:

    def test_any(self):
        class C(ConfigSchema):
            field: Any

        parsed = C('{"field": true}')
        assert parsed.field is True

        parsed = C('{"field": 1}')
        assert_type_value(parsed.field, int, 1)

        parsed = C('{"field": "hi"}')
        assert_type_value(parsed.field, str, 'hi')

    def test_union(self):
        class C(ConfigSchema):
            field: Union[int, str]

    def test_union_err(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Union[int, bytes]

    def test_union_nested(self):
        class C(ConfigSchema):
            field: Union[bool, Union[int, Union[float, str]]]

    def test_union_nested_err(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Union[bool, Union[int, Union[float, bytes]]]

    def test_literal(self):
        class C(ConfigSchema):
            field: Literal[5]

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        with pytest.raises(ValueError):
            C('{"field": 4}')

    def test_literal_multi(self):
        class C(ConfigSchema):
            field: Literal[5, 4]

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        parsed = C('{"field": 4}')
        assert_type_value(parsed.field, int, 4)

        with pytest.raises(ValueError):
            C('{"field": 3}')


class TestNestedSchemas:

    def test_simple(self):
        class C(ConfigSchema):
            nested: _Nested
            class _Nested(ConfigSchema):
                field: int

        parsed = C('{"nested": {"field": 1}}')
        assert isinstance(parsed.nested, C._Nested)
        assert_type_value(parsed.nested.field, int, 1)

    def test_same_field_names(self):
        class C(ConfigSchema):
            field: str
            nested: _Nested
            class _Nested(ConfigSchema):
                field: int

        parsed = C('{"field": "hi", "nested": {"field": 1}}')
        assert_type_value(parsed.field, str, "hi")
        assert isinstance(parsed.nested, C._Nested)
        assert_type_value(parsed.nested.field, int, 1)

    def test_super_nested(self):
        class C(ConfigSchema):
            nested1: _Nested
            class _Nested(ConfigSchema):
                nested2: _Nested
                class _Nested(ConfigSchema):
                    nested3: _Nested
                    class _Nested(ConfigSchema):
                        field: str

        parsed = C('''
            {
                "nested1": {
                    "nested2": {
                        "nested3": {
                            "field": "hi"
                        }
                    }
                }
            }
        ''')
        assert_type_value(parsed.nested1.nested2.nested3.field, str, 'hi')


class TestDefaults:

    @staticmethod
    @pytest.fixture
    def simple_schema():
        class C(ConfigSchema):
            intField = 3
            strField = 'hi'
        return C

    @staticmethod
    @pytest.fixture
    def tuple_schema():
        class C(ConfigSchema):
            field = (1, 2, 3)
        return C

    @staticmethod
    @pytest.fixture
    def list_schema():
        class C(ConfigSchema):
            field = [1, 2, 3]
        return C

    @staticmethod
    @pytest.fixture
    def dict_schema():
        class C(ConfigSchema):
            field = {'one': 1, 'two': 2}
        return C

    def test_empty(self, simple_schema):
        parsed = simple_schema('{}')
        assert_type_value(parsed.intField, int, 3)
        assert_type_value(parsed.strField, str, 'hi')

    def test_any(self):
        class C(ConfigSchema):
            field: Any = 1

        parsed = C('{}')
        assert_type_value(parsed.field, int, 1)

        parsed = C('{"field": 2}')
        assert_type_value(parsed.field, int, 2)

        parsed = C('{"field": "hi"}')
        assert_type_value(parsed.field, str, 'hi')

    def test_missing_one(self, simple_schema):
        parsed = simple_schema('{"intField": 2}')
        assert_type_value(parsed.intField, int, 2)
        assert_type_value(parsed.strField, str, 'hi')

        parsed = simple_schema('{"strField": "hello"}')
        assert_type_value(parsed.intField, int, 3)
        assert_type_value(parsed.strField, str, 'hello')

    def test_bad_type_parsing(self, simple_schema):
        with pytest.raises(TypeError):
            parsed = simple_schema('{"strField": 5}')

    def test_bad_type_definition(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: int = 'hi'

    def test_tuple(self, tuple_schema):
        parsed = tuple_schema('{}')
        assert parsed.field == (1, 2, 3)

    def test_tuple_type_inference(self, tuple_schema):
        parsed = tuple_schema('{"field": [3, 4, 5]}')
        assert parsed.field == (3, 4, 5)

        with pytest.raises(TypeError):
            # We have to keep the same number of items, otherwise ValueError
            # will raise for unequal tuple lengths
            parsed = tuple_schema('{"field": ["hi", "there", "friend"]}')

    def test_list(self, list_schema):
        parsed1 = list_schema('{}')
        assert parsed1.field == [1, 2, 3]

    def test_list_type_inference(self, list_schema):
        parsed = list_schema('{"field": [3, 4, 5]}')
        assert parsed.field == [3, 4, 5]

        with pytest.raises(TypeError):
            parsed = list_schema('{"field": ["hi", "there"]}')

    def test_list_identity(self, list_schema):
        parsed1 = list_schema('{}')
        parsed2 = list_schema('{}')
        assert parsed1.field == [1, 2, 3]
        assert parsed2.field == [1, 2, 3]
        assert parsed2.field is not parsed1.field

    def test_dict(self, dict_schema):
        parsed1 = dict_schema('{}')
        assert parsed1.field == {'one': 1, 'two': 2}

    def test_dict_type_inference(self):
        class C(ConfigSchema):
            field = {'one': 1, 'two': 'two', 'three': True, 'four': 4}

        # noinspection PyUnresolvedReferences
        field_type = C._ConfigSchema__fields['field'][0]
        assert field_type == dict[str, Union[int, str, bool]]

    def test_dict_type_inference_key_not_str(self):
        with pytest.raises(ConfigSchemaError, match=r'key.+str'):
            class C(ConfigSchema):
                field = {'one': 1, 2: "two"}
