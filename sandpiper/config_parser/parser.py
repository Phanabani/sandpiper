import json
from typing import *
from typing import TextIO

from .exceptions import MissingFieldError, ParsingError
from .misc import qualified

__all__ = ('ConfigCompound',)

NoDefault = object()


class ConfigCompound:

    __config_path: str

    @overload
    def __init__(self, config: Union[dict, str, TextIO]):
        pass

    def __init__(self, config: Union[dict, str, TextIO], _config_path=''):
        self.__config_path = _config_path
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

        encountered = set()
        for field_name, default in self.__dict__.items():
            encountered.add(field_name)
            if field_name.startswith('_'):
                continue
            field_type = type(default)
            self.__parse_field(json_parsed, field_name, field_type)

        for field_name, field_type in self.__annotations__.items():
            if field_name in encountered or field_name.startswith('_'):
                continue
            self.__parse_field(json_parsed, field_name, field_type)

    def __parse_field(
            self, json_parsed: Dict[str, Any], field_name: str,
            field_type: Type, default: Any = NoDefault
    ):
        if issubclass(field_type, ConfigCompound):
            assert default is NoDefault, (
                f"Config field {qualified(self.__config_path, field_name)} "
                f"is annotated as a compound and should not have a default "
                f"value"
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
                raise MissingFieldError(self.__config_path, field_name)

            assert isinstance(default, field_type), (
                f"Default value for {qualified(self.__config_path, field_name)} "
                f"({default!r}, type={type(default)}) is not of annotated "
                f"type {field_type}"
            )
            final_value = default
        else:
            # No default was used
            if not isinstance(value, field_type):
                # Try coercing the value into the target type
                try:
                    final_value = field_type(value)
                except Exception as e:
                    raise ParsingError(value, field_type, e)
            else:
                final_value = value

        setattr(self, field_name, final_value)

