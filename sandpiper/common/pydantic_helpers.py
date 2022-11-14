from pathlib import Path
from typing import Any, Callable, Type, TypeVar, Union

from pydantic import BaseModel, ConfigError, root_validator, validator
from pydantic.fields import FieldInfo

from sandpiper.common.typing import (
    T_MaybeList,
    ensure_list,
    get_function_args_annotations,
)

__all__ = [
    "Factory",
    "instance_list_factory",
    "maybe_relative_path",
    "only_one_of",
    "FieldConverterError",
    "FieldConverter",
    "update_forward_refs_recursive",
]

V = TypeVar("V")


class Factory(FieldInfo):
    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(*args, default_factory=default_factory, **kwargs)


def instance_list_factory(class_: Type[V], *args, **kwargs) -> Callable[[], list[V]]:
    def make_list():
        return [class_(*args, **kwargs)]

    return make_list


def maybe_relative_path(fields: T_MaybeList[str], root_path: Path):
    fields = ensure_list(fields)

    def validate_fn(path: Union[Path, str]):
        if not isinstance(path, Path):
            path = Path(path)
        if not path.is_absolute():
            return root_path / path
        return path

    return validator(*fields, allow_reuse=True)(validate_fn)


def only_one_of(
    *groups_of_fields: T_MaybeList[str], need_all: Union[bool, list[bool]] = True
):
    """
    A Pydantic root validator that ensures one and only one of the groups of
    fields exists in the model.

    :param groups_of_fields: the groups of fields that you want one and only
        one of. Each group may be either a list of field names or a single
        field name.
    :param need_all: whether the groups need all fields or just one to succeed.
        If this arg is a bool, apply to all fields. If it's a list of bools,
        each item will be matched up with the corresponding field group from
        `groups_of_fields` (the list lengths must match).
    """
    if isinstance(need_all, list) and len(need_all) != len(groups_of_fields):
        raise ConfigError(
            "`need_all` must either be a bool or a list of bools of the same "
            "length as `groups_of_fields`"
        )

    groups_of_fields = list(groups_of_fields)
    for idx, group in enumerate(groups_of_fields):
        groups_of_fields[idx] = ensure_list(group)

    def validate_fn(cls, values: dict[str, Any]):
        a_group_succeeded = False

        for idx, group in enumerate(groups_of_fields):
            required: bool = need_all[idx] if isinstance(need_all, list) else need_all
            existing_fields = [name in values for name in group]

            # Ignore if no fields exist
            if not any(existing_fields):
                continue

            # Two groups coexist, not allowed!
            if a_group_succeeded:
                raise ValueError(
                    f"Only one of the following groups of fields is allowed: "
                    f"{', '.join(map(str, groups_of_fields))}"
                )

            # Check that all fields exist if that was requested
            if required and not all(existing_fields):
                found = [name for name in group if name in values]
                missing = [name for name in group if name not in values]
                raise ValueError(
                    f"The fields {found} exist, but the following are also "
                    f"required and missing: {missing}"
                )

            # If we've made it here, this group has succeeded
            a_group_succeeded = True

        if not a_group_succeeded:
            raise ValueError(
                f"One and only one of the following groups must exist: "
                f"{', '.join(map(str, groups_of_fields))}"
            )

        return values

    return root_validator(pre=True, allow_reuse=True)(validate_fn)


class FieldConverterError(Exception):
    pass


T_Converter = Callable[[Type["FieldConverterBase"], Any], Any]


class FieldConverter:
    _pyd_converters: dict[type, T_Converter] = None
    _pyd_converter_prefix = "_pyd_convert"

    @classmethod
    def __get_validators__(cls):
        yield cls._pyd_convert

    @classmethod
    def _pyd_get_converters(cls) -> dict[type, T_Converter]:
        if cls._pyd_converters is not None:
            return cls._pyd_converters

        converters: dict[type, T_Converter] = {}
        for name, member in cls.__dict__.items():
            # Iterate through this class's members and find converter methods
            if not isinstance(member, classmethod):
                continue
            if not name.startswith(cls._pyd_converter_prefix):
                continue

            # Check that the converter method has a single value argument and
            # that the type doesn't already have a converter
            fn = member.__func__  # Unwrap classmethod
            fn_args_types = list(get_function_args_annotations(fn).values())
            if len(fn_args_types) != 1:
                raise FieldConverterError(
                    f"Converter {name} must take one positional argument: value"
                )
            converter_type = fn_args_types[0]
            if converter_type in converters:
                raise FieldConverterError(
                    f"Multiple converters found for type {converter_type}, there "
                    f"should only be one"
                )
            converters[converter_type] = fn

        cls._pyd_converters = converters
        return cls._pyd_converters

    @classmethod
    def _pyd_convert(cls, value):
        converters = cls._pyd_get_converters()
        try:
            fn = converters[type(value)]
        except KeyError:
            raise TypeError(f"No converter for type {type(value)}")
        return fn(cls, value)


def update_forward_refs_recursive(model: Type[BaseModel]) -> Type[BaseModel]:
    for name, value in model.__dict__.items():
        if isinstance(value, type) and issubclass(value, BaseModel):
            update_forward_refs_recursive(value)

    model.update_forward_refs(**model.__dict__)
    return model
