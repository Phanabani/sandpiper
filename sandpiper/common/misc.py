from typing import *

__all__ = ('join', 'prune', 'RuntimeMessages')


def join(*fragments, sep=''):
    return sep.join(str(f) for f in fragments if f)


def prune(iterable: Iterable):
    return (i for i in iterable if i)


class RuntimeMessages:

    __slots__ = ('info', 'exceptions')

    info: List[str]
    exceptions: List[Exception]

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
