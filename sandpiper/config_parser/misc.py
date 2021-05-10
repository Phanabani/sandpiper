from typing import Any, NoReturn, Union

__all__ = ('qualified', 'typecheck')


def qualified(parent: str, name: str) -> str:
    return (parent + '.' if parent else '') + name


def typecheck(
        type_: Union[type, tuple[type, ...]], value, name: str
) -> NoReturn:
    if isinstance(type_, tuple):
        condition = type(value) not in type_
    else:
        condition = type(value) is not type_

    if condition:
        raise TypeError(
            f"{name}={value} must be "
            f"{'one ' if isinstance(type_, tuple) else ''}"
            f"of type {type_}, not {type(value)}"
        )
