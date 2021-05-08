import inspect
import re
from types import TracebackType
from typing import Any, Optional

__all__ = (
    'ConfigSchemaError', 'ConfigParsingError', 'MissingFieldError',
    'ParsingError'
)


class _RaiseAtClassMemberException(Exception):

    def __init__(
            self, cls: type, member_name: str, msg: str
    ):
        self.cls = cls
        self.member_name = member_name
        self.msg = msg

        line = _find_class_member_line(cls, member_name)
        if line is not None:
            tb = TracebackType(
                tb_next=None, tb_frame=inspect.currentframe(),
                tb_lasti=0, tb_lineno=line
            )
            self.with_traceback(tb)


_find_indent_pattern = re.compile(r'([ \t]+)[a-zA-Z]')


def _find_class_member_line(cls: type, member_name: str) -> Optional[int]:
    if not isinstance(cls, type):
        raise TypeError(f"cls must be a class, got {type(cls)}")

    member_pattern = re.compile(
        rf'([ \t]+){member_name} *[:=]'
    )

    first = True
    indent = None
    lines, start_line = inspect.getsourcelines(cls)
    for i, line in enumerate(lines):
        if first:
            first = False
            continue
        if indent is None and (m := _find_indent_pattern.match(line)):
            # Store the indentation level for the first expression in
            # the class body
            indent = m[1]
        if (indent is not None
                and (m := member_pattern.match(line))
                and m[1] == indent
        ):
            # Found the member definition
            return start_line + i
    return None


class ConfigSchemaError(_RaiseAtClassMemberException):

    def __str__(self):
        return (
            f"Field {self.member_name} in {self.cls.__qualname__} is "
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
            self, value: Any, target_type: type, base_exc: Exception,
            qualified_name: str = ''
    ):
        self.value = value
        self.target_type = target_type
        self.base_exc = base_exc
        self.qualified_name = qualified_name

    def __str__(self):
        return (
            f"Failed to parse config value ("
            f"qualified_name={self.qualified_name} value={self.value!r} "
            f"target_type={self.target_type} exc=\"{self.base_exc}\""
            f")"
        )
