from collections.abc import Iterable, Sequence
from typing import Optional, Union

__all__ = ['join', 'prune', 'listify', 'RuntimeMessages']


def join(*fragments, sep=''):
    return sep.join(str(f) for f in fragments if f)


def prune(iterable: Iterable):
    return (i for i in iterable if i)


def listify(it: Sequence, trim_after: Optional[int] = None) -> str:
    if len(it) == 0:
        return ''
    if len(it) == 1:
        return str(it[0])
    if len(it) == 2:
        return f"{it[0]} and {it[1]}"
    if trim_after is not None:
        return f"{', '.join(it[:trim_after])}, and {len(it) - trim_after} others"
    return f"{', '.join(it[:-1])}, and {it[-1]}"


class RuntimeMessages:

    __slots__ = ('info', 'exceptions')

    info: list[str]
    exceptions: list[Exception]

    def __init__(self):
        self.info = []
        self.exceptions = []

    def __bool__(self):
        return self.info or self.exceptions

    def __iadd__(self, item: Union[str, Exception]):
        if isinstance(item, str):
            self.info.append(item)
        elif isinstance(item, Exception):
            self.exceptions.append(item)
        else:
            raise ValueError('item must be of type str or Exception')
        return self

    def add_type_once(self, exc: Exception):
        for i in self.exceptions:
            if isinstance(i, type(exc)):
                return
        self.exceptions.append(exc)
