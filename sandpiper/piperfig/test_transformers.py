from textwrap import dedent
import unittest.mock as mock
from pathlib import Path
from typing import Annotated

import pytest

from .exceptions import *
from .parser import *
from .transformers import *


def assert_type_value(value, assert_type: type, assert_value):
    __tracebackhide__ = True
    assert isinstance(value, assert_type)
    assert value == assert_value


def dedent_strip(str_: str) -> str:
    return dedent(str_).strip()


class TestMisc:

    def test_no_annotated(self):
        with pytest.raises(ConfigSchemaError, match=r'Annotated'):
            class C(ConfigSchema):
                field: FromType(int, str)

    def test_bad_origin(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Annotated[Path, '']

    @pytest.mark.skip(
        "I'm not sure how to handle this yet, but it's a bit of an edge case"
    )
    def test_bounded_before_fromtype(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Annotated[int, Bounded(5, 6), FromType(str, int)]

    def test_transform_back_chain(self):
        class C(ConfigSchema):
            # noinspection PyTypeHints
            field: Annotated[
                Path,
                FromType(str, float), FromType(float, int), FromType(int, str),
                MaybeRelativePath(Path('/root/dir'))
            ]

        parsed = C('{"field": "5.3"}')
        assert parsed.field == Path('/root/dir/5')
        serialized = parsed.serialize()
        assert_type_value(
            serialized, str,
            dedent_strip('''
            {
                "field": "5.0"
            }
            ''')
        )


class TestFromType:

    def test_implicit_to(self):
        class C(ConfigSchema):
            field: Annotated[str, FromType(int)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123")

        with pytest.raises(TypeError):
            C('{"field": "123"}')

    def test_multiple_implicit_to_type_err(self):
        with pytest.raises(ConfigSchemaError, match='implicit'):
            class C(ConfigSchema):
                field: Annotated[str, FromType(int), FromType(str)]

    def test_explicit_to(self):
        class C(ConfigSchema):
            field: Annotated[str, FromType(int, str)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123")

    def test_explicit_to_chained(self):
        class C(ConfigSchema):
            field: Annotated[str, FromType(int, float), FromType(float, str)]

        parsed = C('{"field": 123}')
        assert_type_value(parsed.field, str, "123.0")

    def test_explicit_to_type_mismatch(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Annotated[str, FromType(int, float)]

    def test_implicit_with_bounded_after(self):
        # I want the shorthand implicit notation available if it's used at
        # the last FromType, however I think it's difficult to understand
        # what's going on if more transformers come after it
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Annotated[int, FromType(str), Bounded(2, 4)]

    def test_explicit_with_bounded_after(self):
        class C(ConfigSchema):
            field: Annotated[int, FromType(str, int), Bounded(2, 4)]

        parsed = C('{"field": "3"}')
        assert_type_value(parsed.field, int, 3)

        with pytest.raises(ValueError):
            parsed = C('{"field": "5"}')

    def test_invalid_from_type(self):
        with pytest.raises(ConfigSchemaError):
            class C(ConfigSchema):
                field: Annotated[int, FromType(Path, int)]

    def test_back(self):
        trans = FromType(int, str)
        back = trans.transform_back("5")
        assert_type_value(back, int, 5)

    def test_back_err(self):
        trans = FromType(int, str)
        with pytest.raises(TypeError):
            back = trans.transform_back(True)


class TestBounded:

    def test_min(self):
        class C(ConfigSchema):
            field: Annotated[int, Bounded(5, None)]

        with pytest.raises(ValueError):
            C('{"field": 4}')

        parsed = C('{"field": 5}')
        assert_type_value(parsed.field, int, 5)

        parsed = C('{"field": 6}')
        assert_type_value(parsed.field, int, 6)

    def test_max(self):
        class C(ConfigSchema):
            field: Annotated[int, Bounded(None, 10)]

        parsed = C('{"field": 9}')
        assert_type_value(parsed.field, int, 9)

        parsed = C('{"field": 10}')
        assert_type_value(parsed.field, int, 10)

        with pytest.raises(ValueError):
            C('{"field": 11}')

    def test_min_max(self):
        class C(ConfigSchema):
            field: Annotated[int, Bounded(2, 4)]

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

    def test_min_equal_to_max(self):
        class C(ConfigSchema):
            field: Annotated[int, Bounded(2, 2)]

        with pytest.raises(ValueError):
            C('{"field": 1}')

        parsed = C('{"field": 2}')
        assert_type_value(parsed.field, int, 2)

        with pytest.raises(ValueError):
            C('{"field": 3}')

    def test_min_greater_than_max(self):
        with pytest.raises(ValueError):
            class C(ConfigSchema):
                field: Annotated[int, Bounded(2, 1)]

    def test_back(self):
        trans = Bounded(2, 4)
        back = trans.transform_back(3)
        assert_type_value(back, int, 3)

    def test_back_err(self):
        trans = Bounded(2, 4)
        with pytest.raises(ValueError):
            back = trans.transform_back(5)


# Let's use Posix paths for our tests
@mock.patch('pathlib.os.name', 'posix')
@mock.patch('pathlib._PosixFlavour.is_supported', True)
class TestMaybeRelativePath:

    def test_relative(self):
        class C(ConfigSchema):
            # noinspection PyTypeHints
            field: Annotated[Path, MaybeRelativePath(Path('/root/dir'))]

        parsed = C('{"field": "relative/path"}')
        assert parsed.field == Path('/root/dir/relative/path')

    def test_relative_with_dot(self):
        class C(ConfigSchema):
            # noinspection PyTypeHints
            field: Annotated[Path, MaybeRelativePath(Path('/root/dir'))]

        parsed = C('{"field": "./relative/path"}')
        assert parsed.field == Path('/root/dir/relative/path')

    def test_absolute(self):
        class C(ConfigSchema):
            # noinspection PyTypeHints
            field: Annotated[Path, MaybeRelativePath(Path('/root/dir'))]

        parsed = C('{"field": "/absolute/path"}')
        assert parsed.field == Path('/absolute/path')

    def test_back_relative(self):
        trans = MaybeRelativePath(Path('/root/dir'))
        path = Path('/root/dir/relative/path')
        back = trans.transform_back(path)
        assert_type_value(back, str, 'relative/path')

    def test_back_absolute(self):
        trans = MaybeRelativePath(Path('/root/dir'))
        path = Path('/absolute/path')
        back = trans.transform_back(path)
        assert_type_value(back, str, '/absolute/path')
