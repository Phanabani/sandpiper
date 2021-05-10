from typing import Any, NoReturn, Union

__all__ = ('qualified', 'typecheck')


def qualified(parent: str, name: str) -> str:
    return (parent + '.' if parent else '') + name


def typecheck(
        type_: Union[type, tuple[type, ...]], value, name: str
) -> NoReturn:
    if (not isinstance(value, type_)
            # Turns out that isinstance(True, int) is true. Let's handle that...
            or (type_ is int and isinstance(value, bool))):
        raise TypeError(
            f"{name}={value} must be "
            f"{'one ' if isinstance(type_, tuple) else ''}"
            f"of type {type_}, not {type(value)}"
        )
