from typing import Any

__all__ = (
    "ConfigSchemaError",
    "ConfigParsingError",
    "MissingFieldError",
    "ParsingError",
)


class ConfigSchemaError(Exception):
    def __init__(self, cls: type, field_name: str, msg: str):
        self.cls = cls
        self.field_name = field_name
        self.msg = msg

    def __str__(self):
        return (
            f"Field {self.field_name} in {self.cls.__qualname__} is "
            f"invalid: {self.msg}"
        )


class ConfigParsingError(Exception):
    pass


class MissingFieldError(ConfigParsingError):
    def __init__(self, qualified_name: str):
        self.qualified_name = qualified_name

    def __str__(self):
        return f"Missing required field {self.qualified_name}"


class ParsingError(ConfigParsingError):
    def __init__(
        self,
        value: Any,
        target_type: type,
        base_exc: Exception,
        qualified_name: str = "",
    ):
        self.value = value
        self.target_type = target_type
        self.base_exc = base_exc
        self.qualified_name = qualified_name

    def __str__(self):
        return (
            f"Failed to parse config value ("
            f"qualified_name={self.qualified_name} value={self.value!r} "
            f'target_type={self.target_type} exc="{self.base_exc}"'
            f")"
        )
