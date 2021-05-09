from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, Union

from .exceptions import ConfigSchemaError
from .misc import typecheck

__all__ = (
    'do_transformations', 'ConfigTransformer', 'FromType',
    'Bounded', 'MaybeRelativePath'
)

V1 = TypeVar('V1')
V2 = TypeVar('V2')
T_Target = TypeVar('T_Target')


def do_transformations(value, annotation):
    if (not hasattr(annotation, '__origin__')
            or not hasattr(annotation, '__metadata__')):
        raise TypeError(f"Value {annotation} is not an Annotated instance")

    target_type: type = annotation.__origin__
    metadata: tuple = annotation.__metadata__
    for transformer in metadata:
        if not isinstance(transformer, ConfigTransformer):
            raise ConfigSchemaError() from TypeError(
                f"Annotation metadata {transformer} must be an instance of "
                f"{ConfigTransformer.__name__}"
            )
        value = transformer.transform(value, target_type)
    return value


class ConfigTransformer(metaclass=ABCMeta):

    @abstractmethod
    def transform(self, value: Any, target_type: type) -> Any:
        pass


class FromType(ConfigTransformer):

    # TODO update to generic type[] once jetbrains fixes a bug in pycharm
    def __init__(
            self, from_type: Type[V1], to_type: Optional[Type[V2]] = None
    ):
        self.from_type = from_type
        self.to_type = to_type

    def transform(
            self, value: V1, target_type: Type[T_Target]
    ) -> Union[T_Target, V2]:
        typecheck(self.from_type, value, 'value')
        if self.to_type is not None:
            return self.to_type(value)
        return target_type(value)


# noinspection PyShadowingBuiltins
class Bounded(ConfigTransformer):

    def __init__(self, min: Optional[V1], max: Optional[V1]):
        if min is not None and max is not None:
            if type(min) != type(max):
                raise ConfigSchemaError() from TypeError(
                    f"min and max must be the same type, got {type(min)} and "
                    f"{type(max)}"
                )
            if min > max:
                raise ConfigSchemaError() from ValueError(
                    f"min {min} is greater than max {max}"
                )
        self.type = type(min)
        self.min = min
        self.max = max

    def transform(self, value: V1, target_type: type) -> V1:
        typecheck(self.type, value, 'value')
        try:
            if self.min is not None and value < self.min:
                raise ValueError(
                    f"Value {value} must be greater than or equal to {self.min}"
                )
            if self.max is not None and value > self.max:
                raise ValueError(
                    f"Value {value} must be less than or equal to {self.max}"
                )
        except TypeError:
            raise ConfigSchemaError()
        return value


class MaybeRelativePath(ConfigTransformer):

    def __init__(self, root_path: Path):
        if not isinstance(root_path, Path):
            raise ConfigSchemaError() from TypeError(
                f"root_path must be of type Path, got {type(root_path)}"
            )
        self.root_path = root_path

    def transform(self, value: str, target_type: Type[T_Target]) -> Path:
        typecheck(str, value, 'value')
        path = Path(value)
        if not path.is_absolute():
            return self.root_path / path
        return path
