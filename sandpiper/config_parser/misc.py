from typing import *

__all__ = ('qualified', 'typecheck')


def qualified(parent: str, name: str) -> str:
    return (parent + '.' if parent else '') + name


def typecheck(
        type_: Union[Type, Tuple[Type, ...]], **names_and_values: Any
) -> NoReturn:
    for name, value in names_and_values.items():
        if not isinstance(value, type_):
            raise TypeError(
                f"{name}={value} must be "
                f"{'one ' if isinstance(type_, tuple) else ''}"
                f"of type {type_}, not {type(value)}"
            )
