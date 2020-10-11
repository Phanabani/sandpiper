from typing import Iterable

__all__ = ['prune']


def prune(iterable: Iterable):
    return (i for i in iterable if i)


def join(*fragments):
    return ''.join(str(f) for f in fragments if f)
