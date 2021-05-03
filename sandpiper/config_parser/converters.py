from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from .misc import typecheck

__all__ = (
    'Convert', 'BoundedInt', 'MaybeRelativePath'
)


class ConfigConverterBase(metaclass=ABCMeta):

    @abstractmethod
    def convert(self, value: Any) -> Any:
        pass

    @classmethod
    def _check_tuple(
            cls, tuple_: tuple, *field_names: str
    ) -> tuple:
        if len(tuple_) != len(field_names):
            raise ValueError(
                f"Missing type arguments. Expected "
                f"{cls.__name__}[{', '.join(field_names)}]"
            )
        return tuple_


V_Base = TypeVar('V_Base')
V_Target = TypeVar('V_Target')


class Convert(ConfigConverterBase):
    """
    Convert[base_type: Type, target_type: Type]

    Annotate a config field with this type to convert the field from `base_type`
    to `target_type`. `target_type`'s constructor will be called with the
    field's value as its only positional argument.

    Example:
        log_file: Convert[str, Path]
    """

    # TODO update to generic type[] once jetbrains fixes a bug in pycharm
    def __init__(self, base_type: Type[V_Base], target_type: Type[V_Target]):
        typecheck(type, base_type=base_type, target_type=target_type)
        self.base_type = base_type
        self.target_type = target_type

    def __class_getitem__(
            cls, base_and_target_types: tuple[Type[V_Base], Type[V_Target]]
    ):
        base_type, target_type = cls._check_tuple(
            base_and_target_types, 'base_type', 'target_type'
        )
        return cls(base_type, target_type)

    def convert(self, value: V_Base) -> V_Target:
        if not isinstance(value, self.base_type):
            raise TypeError(f'Expected type {self.base_type}, got {type(value)}')
        return self.target_type(value)


# noinspection PyMissingConstructor
class BoundedInt(int, ConfigConverterBase):
    """
    BoundedInt[min: int, max: int]

    Annotate a config field with this type to ensure the field's value is an
    int where value >= `min` and value <= `max`. `min` and/or `max` may be None
    to specify no lower or upper bound, respectively.

    Example:
        threads: BoundedInt[1, 8]
        connection_retries: BoundedInt[1, None]
    """

    def __init__(self, min: Optional[int], max: Optional[int]):
        typecheck((int, type(None)), min=min, max=max)
        self._converter_min = min
        self._converter_max = max

    def __class_getitem__(cls, min_max: tuple[Optional[int], Optional[int]]):
        cls._check_tuple(min_max, 'min', 'max')
        return cls(min=min_max[0], max=min_max[1])

    def convert(self, value: Any) -> int:
        typecheck(int, value=value)
        if self._converter_min is not None and value < self._converter_min:
            raise ValueError(
                f"Value must be greater than or equal to {self._converter_min}"
            )
        if self._converter_max is not None and value > self._converter_max:
            raise ValueError(
                f"Value must be less than or equal to {self._converter_max}"
            )
        return value


class MaybeRelativePath(Path, ConfigConverterBase):
    """
    MaybeRelativePath[root: Path]

    Annotate a config field with this type to convert a string to a Path. If
    the path is not an absolute path, it will be used as a path relative to
    `root`.

    Example:
        logs_directory: MaybeRelativePath['/my/project/root']
    """

    def __init__(self, root: Path):
        typecheck(Path, root=root)
        self._converter_root = root

    def __class_getitem__(cls, root: Path):
        return cls(root=root)

    def convert(self, value: str) -> Path:
        typecheck(str, value=value)
        path = Path(value)
        if not path.is_absolute():
            return self._converter_root / path
        return path
