from typing import Iterable

__all__ = ['join', 'prune']


def join(*fragments, sep=''):
    return sep.join(str(f) for f in fragments if f)


def prune(iterable: Iterable):
    return (i for i in iterable if i)
