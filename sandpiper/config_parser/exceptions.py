from typing import Any, Type

from .misc import qualified

__all__ = ('MissingFieldError', 'ParsingError')


class MissingFieldError(Exception):

    def __init__(self, field_parent: str, field_name: str):
        self.field_parent = field_parent
        self.field_name = field_name

    def __str__(self):
        return (
            "Missing required field "
            + qualified(self.field_parent, self.field_name)
        )


class ParsingError(Exception):

    def __init__(self, value: Any, target_type: Type, base_exc: Exception):
        self.value = value
        self.target_type = target_type
        self.base_exc = base_exc

    def __str__(self):
        return (
            f"Failed to parse {self.value!r} as {self.target_type}"
        )