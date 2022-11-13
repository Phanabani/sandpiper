__all__ = ["qualified", "typecheck"]

from typing import NoReturn, Union


def qualified(parent: str, name: str) -> str:
    return (parent + "." if parent else "") + name


def typecheck(
    type_: Union[type, tuple[type, ...]], value, name: str, use_isinstance=False
) -> NoReturn:
    if use_isinstance:
        is_type = isinstance(value, type_)
    else:
        if isinstance(type_, tuple):
            is_type = type(value) in type_
        else:
            is_type = type(value) is type_

    if not is_type:
        raise TypeError(
            f"{name}={value} must be "
            f"{'one ' if isinstance(type_, tuple) else ''}"
            f"of type {type_}, not {type(value)}"
        )
