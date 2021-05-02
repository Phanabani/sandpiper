import json
from typing import *
from typing import TextIO

from .converters import ConfigConverter
from .exceptions import MissingFieldError, ParsingError
from .misc import qualified

__all__ = ('ConfigCompound',)

NoDefault = object()


class ConfigCompound:

    __path: str

    @overload
    def __init__(self, config: Union[dict, str, TextIO]):
        pass

    def __init__(self, config: Union[dict, str, TextIO], _compound_path=''):
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
            field_type: Type, default: Any = NoDefault
    ):
        qualified_name = qualified(self.__path, field_name)
        if issubclass(field_type, ConfigCompound):
            assert default is NoDefault, (
                f"Config field {qualified_name} is annotated as a compound "
                f"and should not have a default value"
            )
            # The type is a compound tag, so pass the json-parsed dict into
            # the compound type for further parsing
            final_value = field_type(json_parsed.get(field_name, {}))
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

    def __convert(self, value: Any, type_: Union[ConfigConverter, Type]):
        if isinstance(type_, ConfigConverter):
            # Use the special converter
            return type_.convert(value)

        if not isinstance(value, type_):
            # Try coercing the value into the target type
            try:
                return type_(value)
            except Exception as e:
                raise ParsingError(value, type_, e)

        return value
