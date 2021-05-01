from typing import *

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

    def __init__(
            self, value: Any, target_type: Type, base_exc: Exception,
            field_parent: str = '', field_name: str = ''
    ):
        self.value = value
        self.target_type = target_type
        self.base_exc = base_exc
        self.add_field_info(field_parent, field_name)

    def add_field_info(self, parent: str, name: str):
        self.field_path = qualified(parent, name)

    def __str__(self):
        return (
            f"Failed to parse config value (path={self.field_path} "
            f"value={self.value!r} target_type={self.target_type} "
            f"exc=\"{self.base_exc}\")"
        )
