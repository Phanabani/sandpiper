from functools import cached_property
import json
import sys
from types import MethodType
from typing import (
    Any, Annotated as A, Literal, NoReturn, TextIO, Union, get_type_hints
)

from .exceptions import *
from .misc import *
from .transformers import *

__all__ = ('ConfigSchema',)

NoDefault = object()


def is_json_type(type_: type) -> bool:
    return type_ in (type(None), bool, int, float, str, list, dict)


def should_skip(name: str, value: Any = None) -> bool:
    return (
        name.startswith('_')
        or (
            value is not None
            and isinstance(value, (MethodType, cached_property))
        )
    )


class ConfigSchema:

    __path: str
    __fields: dict[str, tuple[A[Any, 'Type'], A[Any, 'Default']]]

    def __init__(self, config: Union[dict, str, TextIO], *, _schema_path=''):
        self.__path = _schema_path
        self.__parse(config)

    def __init_subclass__(cls, /, **kwargs):
        """
        Compute annotations and defaults at subclass definition time. We don't
        need to recompute them every single parse. This also allows for schema
        errors to be risen early, rather than when the user's input is being
        parsed.
        """
        super().__init_subclass__(**kwargs)

        annotations = get_type_hints(
            cls,
            globalns=vars(sys.modules[cls.__module__]),
            localns=vars(cls),
            include_extras=True
        )
        cls_dict = cls.__dict__

        cls.__fields = {}
        encountered = set()

        # Iterate through annotations to get fields with type annotations
        for field_name, field_type in annotations.items():
            encountered.add(field_name)
            if should_skip(field_name):
                continue
            default = cls_dict.get(field_name, NoDefault)
            if default is not NoDefault:
                # Try to convert this default. If an error is raised, the value
                # does not match the annotation.
                try:
                    _convert(default, field_type, field_name)
                except Exception:
                    raise ConfigSchemaError(
                        cls, field_name,
                        f"Default value {default} does not match type "
                        f"annotation {field_type}"
                    )
            cls.__fields[field_name] = field_type, default

        # Iterate through __dict__ to get the remaining fields with default
        # values
        for field_name, default in cls_dict.items():
            if field_name in encountered or should_skip(field_name, default):
                continue
            try:
                field_type = _infer_type(default)
            except TypeError:
                raise ConfigSchemaError(
                    cls, field_name,
                    f"Could not infer type of default value {default}. "
                    f"It's probably an invalid type."
                )
            cls.__fields[field_name] = (field_type, default)

        # Validate the annotations/defaults for each field
        for field_name, field_info in cls.__fields.items():
            field_type, default = field_info
            _validate_annotation(cls, field_name, field_type)

    def __parse(self, config: Union[dict, str, TextIO]):
        if isinstance(config, str):
            config = json.loads(config)
        elif isinstance(config, TextIO):
            config = json.load(config)
        elif isinstance(config, dict):
            config = config
        else:
            raise TypeError(
                f"config must be one of type (dict, str, TextIO), got "
                f"{type(config)}"
            )

        # Iterate through annotations to get fields with type annotations
        for field_name, field_info in self.__class__.__fields.items():
            field_type, default = field_info
            self.__read_field(config, field_name, field_type, default)

    def __read_field(
            self, json_parsed: dict[str, Any], field_name: str,
            field_type: Any, default: Any = NoDefault
    ):
        qualified_name = qualified(self.__path, field_name)
        if (isinstance(field_type, type)
                and issubclass(field_type, ConfigSchema)):
            assert default is NoDefault, (
                f"Config field {qualified_name} is annotated as a schema "
                f"and should not have a default value"
            )
            # The type is a schema, so pass the json-parsed dict into the
            # schema type for further parsing
            final_value = field_type(
                json_parsed.get(field_name, {}),
                _schema_path=qualified_name
            )
            setattr(self, field_name, final_value)
            return

        try:
            value = json_parsed[field_name]
        except KeyError:
            if default is NoDefault:
                raise MissingFieldError(qualified_name)
            value = default
        # We want to convert default values too, so it's just as if they
        # were written by the user
        final_value = _convert(value, field_type, qualified_name)
        setattr(self, field_name, final_value)


def _infer_type(value):
    if isinstance(value, tuple):
        return tuple[tuple(_infer_type(i) for i in value)]

    if isinstance(value, list):
        return list[Union[tuple(_infer_type(i) for i in value)]]

    if isinstance(value, dict):
        if any(not isinstance(i, str) for i in value.keys()):
            raise TypeError('Dict keys must be strings to conform with JSON')
        return dict[str, Union[tuple(_infer_type(i) for i in value.values())]]

    if is_json_type(type(value)):
        return type(value)

    raise TypeError(f"Could not infer type of {value}")


def _validate_annotation(cls: type, field_name: str, type_) -> NoReturn:
    if type_ is Any:
        # Any type is accepted
        return

    if isinstance(type_, ConfigTransformer):
        raise ConfigSchemaError(
            cls, field_name,
            f"You may only use ConfigTransformers as metadata in "
            f"typing.Annotated. Try something like "
            f"Annotated[out_type, {type_!r}]"
        )

    if isinstance(type_, type) and issubclass(type_, ConfigSchema):
        return

    if hasattr(type_, '__metadata__') and hasattr(type_, '__origin__'):
        # We don't need to validate the __origin__ after this because
        # _validate_transformers will check that our types match.
        needs_origin_check = _validate_transformers(cls, field_name, type_)
        if needs_origin_check:
            _validate_annotation(cls, field_name, type_.__origin__)
        return

    if hasattr(type_, '__origin__') and hasattr(type_, '__args__'):
        # Use special rules for typing module types
        type_origin = type_.__origin__
        type_args = type_.__args__

        if type_origin is Union:
            # The subtypes in a union might be other special typing types.
            # Recursively call this function with each subtype
            for subtype in type_args:
                _validate_annotation(cls, field_name, subtype)
            return

        if type_origin is tuple:
            for i, subtype in enumerate(type_args):
                _validate_annotation(cls, field_name, subtype)
            return

        if type_origin is list:
            list_type = type_args[0]
            _validate_annotation(cls, field_name, list_type)
            return

        if type_origin is dict:
            key_type, value_type = type_args
            if key_type is not str:
                raise TypeError(
                    f"Dict keys can only be strings (to conform with JSON), "
                )
            _validate_annotation(cls, field_name, value_type)
            return

        if type_origin is Literal:
            for literal in type_args:
                if isinstance(literal, list) or not is_json_type(type(literal)):
                    raise ConfigSchemaError(
                        cls, field_name,
                        f"Literal values may only be instances of NoneType, "
                        f"bool, int, float, or str"
                    )
            return

        raise ConfigSchemaError(
            cls, field_name,
            f"Special type annotation {type_origin} is not accepted."
        )

    if type_ is tuple:
        # Special case
        return

    if is_json_type(type_):
        # Simple type
        return

    # Some other annotation we can't handle
    raise ConfigSchemaError(
        cls, field_name,
        f"Type annotation {type_} is not accepted. Maybe you want to use the "
        f"FromType transformer?"
    )


def _validate_transformers(cls: type, field_name: str, type_) -> bool:
    """
    :return: whether the origin type needs additional type checking
    """
    target_type = type_.__origin__

    prev_type = None
    first_fromtype_encountered = False
    implicit_fromtype_encountered = False
    for trans in type_.__metadata__:
        if not isinstance(trans, ConfigTransformer):
            # Skip unknown annotations (rather than raising)
            continue

        if implicit_fromtype_encountered:
            # Implicit to_type for FromType is only allowed as the last
            # transformer
            raise ConfigSchemaError(
                cls, field_name,
                "A FromType transformer with an implicit to_type may only be "
                "the last transformer in the sequence."
            )

        if prev_type is not None and trans.in_type != prev_type:
            # The input type of this transformer doesn't match the output type
            # of the previous transformer
            raise ConfigSchemaError(
                cls, field_name,
                f"Input type {trans.in_type} of Transformer {trans} does not "
                f"match the output type {prev_type} of the previous transformer"
            )

        prev_type = trans.out_type

        if isinstance(trans, FromType):
            if not first_fromtype_encountered:
                # Check that the from_type of the first FromType is a valid
                # JSON type
                if not is_json_type(trans.from_type):
                    raise ConfigSchemaError(
                        cls, field_name,
                        f"The input type of the first FromType transformer "
                        f"must be a valid JSON type, got {trans.from_type}"
                    )
                first_fromtype_encountered = True

            if trans.to_type is None:
                # Implicit to_type; this may only happen once!
                implicit_fromtype_encountered = True
                prev_type = target_type

    if prev_type is None:
        # The caller should type check the origin type
        return True
    elif target_type is not prev_type:
        raise ConfigSchemaError(
            cls, field_name,
            f"to_type {prev_type} of the final FromType transformer does not "
            f"match the annotated type {target_type} of this field"
        )
    return False


def _convert(
        value: Any, type_: Any, qualified_name: str
):
    if type_ is Any:
        # Any type is accepted
        return value

    if hasattr(type_, '__metadata__'):
        # Annotated with transformers
        return do_transformations(value, type_)

    if hasattr(type_, '__origin__') and hasattr(type_, '__args__'):
        # Use special rules for typing module types
        type_origin = type_.__origin__
        type_args = type_.__args__

        if type_origin is Union:
            # The subtypes in a union might be other special typing types.
            # Recursively call this function with each subtype
            for subtype in type_args:
                try:
                    return _convert(value, subtype, qualified_name)
                except RuntimeError as e:
                    # Something really bad happened, don't ignore
                    raise e
                except Exception:
                    # This is normal, ideally this will happen for all but
                    # one matching subtype
                    pass
            raise ValueError(
                f"Value at {qualified_name} didn't match any type in {type_}"
            )

        if type_origin is tuple:
            # Convert every value in the tuple
            typecheck((list, tuple), value, qualified_name)
            if len(value) != len(type_args):
                raise ValueError(
                    f"Expected a tuple of length {len(type_args)}, got "
                    f"{len(value)}"
                )

            converted_list = []
            for i, subtype in enumerate(type_args):
                converted = _convert(
                    value[i], subtype, f"{qualified_name}[{i}]"
                )
                converted_list.append(converted)
            return tuple(converted_list)

        if type_origin is list:
            # Convert every value in the list
            typecheck(list, value, qualified_name)
            list_type = type_args[0]
            converted_list = []
            for i, subvalue in enumerate(value):
                converted = _convert(
                    subvalue, list_type, f"{qualified_name}[{i}]"
                )
                converted_list.append(converted)
            return converted_list

        if type_origin is dict:
            # Convert every value in the dict
            typecheck(dict, value, qualified_name)
            key_type, value_type = type_args
            if key_type is not str:
                # Ideally should never happen
                raise RuntimeError(
                    "The dict keys type annotation should be str"
                )

            converted_dict = {}
            for key, val in value.items():
                dict_qual_name = f"{qualified_name}[{key}]"
                typecheck(key_type, key, dict_qual_name)
                converted = _convert(
                    val, value_type, dict_qual_name
                )
                converted_dict[key] = converted

            return converted_dict

        if type_origin is Literal:
            # Check equality with one of the literal values
            if value not in type_args:
                raise ValueError(
                    f"Value must be equal to one of {type_args}"
                )
            return value

    if type_ is tuple:
        # Special case -- make tuple from the list
        typecheck((list, tuple), value, qualified_name)
        return tuple(value)

    if is_json_type(type_):
        # Simple typecheck
        typecheck(type_, value, qualified_name)
        return value

    # Ideally should never happen
    raise RuntimeError(
        f"Got unexpected type {type_}. This should've been caught in "
        f"the subclass validation step!"
    )
