from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class UnitMap(Generic[T]):

    _two_way: dict[T, T]
    _one_way: dict[T, T]

    def __init__(self, *, two_way: dict[T, T], one_way: dict[T, T] = None):
        if not isinstance(two_way, dict):
            raise ValueError(f"two_way must be a dict")
        self._two_way = self._create_bidict(two_way)

        one_way = one_way or ()
        if not isinstance(one_way, dict):
            raise ValueError(f"one_way must be dict")
        self._one_way = {}
        for key, value in one_way.items():
            if key in self._two_way:
                raise ValueError(
                    f"Key {key} in one_way is already found in two_way. Its "
                    f"mapping in one_way will never be used."
                )
            self._one_way[key] = value

    def __getitem__(self, key):
        try:
            return self._two_way[key]
        except KeyError:
            try:
                return self._one_way[key]
            except KeyError:
                raise KeyError(f"Key {key} does not exist")

    def __contains__(self, key):
        return key in self._two_way or key in self._one_way

    @staticmethod
    def _create_bidict(dict_: dict[T, T]) -> dict[T, T]:
        out = {}
        for a, b in dict_.items():
            out[a] = b
            out[b] = a
        return out
