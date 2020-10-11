from typing import Iterable

__all__ = ['prune']


def prune(iterable: Iterable):
    return (i for i in iterable if i)
