from __future__ import annotations
from typing import *

T = TypeVar('T')


class PriorityBidict(Generic[T]):

    _priority: Dict[T, T]
    _other: Dict[T, T]

    def __init__(
            self, *, priority: Sequence[Tuple[T, T]],
            other: Sequence[Tuple[T, T]] = None
    ):
        if not isinstance(priority, Sequence):
            raise ValueError(
                f"priority must be a sequence of key-value pair tuples"
            )
        self._priority = {}
        self._set_bidir(priority, self._priority)

        self._other = {}
        if other is not None:
            if not isinstance(other, Sequence):
                raise ValueError(
                    f"other must be None or a sequence of key-value pair tuples"
                )
            self._set_bidir(other, self._other)

    def __getitem__(self, key):
        try:
            return self._priority[key]
        except KeyError:
            try:
                return self._other[key]
            except KeyError:
                raise KeyError(f"Key {key} does not exist")

    def __contains__(self, key):
        return key in self._priority or key in self._other

    @staticmethod
    def _set_bidir(mappings: Sequence[Tuple[T, T]], dict_: Dict):
        for a, b in mappings:
            dict_[a] = b
            dict_[b] = a
