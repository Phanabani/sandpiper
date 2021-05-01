from abc import ABCMeta, abstractmethod
from typing import *


class ConversionFailed(Exception):
    pass


class ConfigConverter(metaclass=ABCMeta):

    @abstractmethod
    def convert(self, value: Any) -> Any:
        pass


class BoundedInt(ConfigConverter):

    def __init__(self, min: Optional[int], max: Optional[int]):
        if (not (min is None or isinstance(min, int))
                or not (max is None or isinstance(max, int))):
            raise TypeError('min and max must be either integers or None')

        self.min = min
        self.max = max

    def __class_getitem__(cls, min_max: Tuple[Optional[int], Optional[int]]):
        if len(min_max) != 2:
            raise ValueError(
                f"You must supply a minimum and maximum value, separated by a "
                f"comma. One or both may be None to specify there is no "
                f"bound in that direction."
            )
        return cls(min=min_max[0], max=min_max[1])

    def convert(self, value: Any) -> int:
        pass

