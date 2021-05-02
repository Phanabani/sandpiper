import json
from typing import *
from typing import TextIO

from .converters import ConfigConverterBase
from .exceptions import *
from .misc import *

__all__ = ('ConfigCompound',)

NoDefault = object()


def is_json_type(value: Any) -> bool:
    return (
        isinstance(value, (list, str, int, float))
        or value in (True, False, None)
    )


class ConfigCompound:

    __path: str

    def __init__(self, config: Union[dict, str, TextIO], *, _compound_path=''):
        self.__path = _compound_path
        self.__parse(config)

    def __parse(self, config: Union[dict, str, TextIO]):
        if isinstance(config, str):
            json_parsed = json.loads(config)
        elif isinstance(config, TextIO):
            json_parsed = json.load(config)
        else:
            raise TypeError(
                f"config must be one of (TextIO, str), got {type(config)}"
            )

        # Iterate through __dict__ to get fields with default values
        encountered = set()
        for field_name, default in self.__dict__.items():
            encountered.add(field_name)
            if field_name.startswith('_'):
                continue
            field_type = type(default)
            self.__read_field(json_parsed, field_name, field_type)

        # Iterate through __annotations__ to get the remaining fields with
        # type annotations
        for field_name, field_type in self.__annotations__.items():
            if field_name in encountered or field_name.startswith('_'):
                continue
            self.__read_field(json_parsed, field_name, field_type)

    def __read_field(
            self, json_parsed: Dict[str, Any], field_name: str,
            field_type: Any, default: Any = NoDefault
    ):
        qualified_name = qualified(self.__path, field_name)
        if issubclass(field_type, ConfigCompound):
            assert default is NoDefault, (
                f"Config field {qualified_name} is annotated as a compound "
                f"and should not have a default value"
            )
            # The type is a compound tag, so pass the json-parsed dict into
            # the compound type for further parsing
            final_value = field_type(
                json_parsed.get(field_name, {}),
                _compound_path=f"{self.__path}.{field_name}"
            )
            setattr(self, field_name, final_value)
            return

        try:
            value = json_parsed[field_name]
        except KeyError:
            if default is NoDefault:
                raise MissingFieldError(qualified_name)
            final_value = default
        else:
            # No default was used
            try:
                final_value = self.__convert(value, field_type, qualified_name)
            except ParsingError as e:
                raise e

        setattr(self, field_name, final_value)

    @staticmethod
    def __convert(
            value: Any, type_: Any, qualified_name: str
    ):
        if isinstance(type_, ConfigConverterBase):
            # Use a converter
            return type_.convert(value)

        if hasattr(type_, '__origin__') and hasattr(type_, '__args__'):
            # Use special rules for typing module types
            type_origin = type_.__origin__
            type_args = type_.__args__

            if type_origin is Union:
                # Typecheck with a tuple of types
                typecheck(type_args, value=value)
                return value

            if type_origin is List:
                # Typecheck every value in the list
                typecheck(list, value=value)
                for i in value:
                    typecheck(type_args[0], value=i)
                return value

            if type_origin is Literal:
                # Check equality with one of the literal values
                if value not in type_args:
                    raise ValueError(
                        f"Value must be equal to one of {type_args}"
                    )
                return value

            raise ConfigSchemaError(
                f"Special type annotation {type_origin} is not accepted."
            )

        if is_json_type(type_):
            # Simple typecheck
            typecheck(type_, value=value)
            return value

        # Some other annotation we can't handle
        raise ConfigSchemaError(
            f"Type annotation {type(type_)} for {qualified_name} is not "
            f"accepted. Maybe you want to use the converters.Convert "
            f"annotation?"
        )
