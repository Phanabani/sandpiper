import sys
from types import FunctionType, MethodType
from typing import Callable, Optional, TypeVar, Union, get_type_hints

__all__ = [
    "T_MaybeList",
    "ensure_list",
    "T_Functionish",
    "get_function_annotations",
    "get_function_args_annotations",
    "get_function_return_type",
]

V = TypeVar("V")
T_MaybeList = Union[V, list[V]]


def ensure_list(value_or_list: T_MaybeList[V]) -> list[V]:
    if not isinstance(value_or_list, list):
        return [value_or_list]
    return value_or_list


T_Functionish = Union[Callable, FunctionType, MethodType, classmethod, staticmethod]


def get_function_annotations(f: T_Functionish):
    try:
        # Unwrap classmethod/staticmethod
        f = f.__func__
    except AttributeError:
        pass
    return get_type_hints(
        f,
        globalns=vars(sys.modules[f.__module__]),
        localns=vars(f),
        include_extras=False,
    )


def get_function_args_annotations(f: T_Functionish) -> dict[str, type]:
    annotations = get_function_annotations(f)
    try:
        del annotations["return"]
    except KeyError:
        pass
    return annotations


def get_function_return_type(f: T_Functionish) -> Optional[type]:
    annotations = get_function_annotations(f)
    return annotations.get("return")
