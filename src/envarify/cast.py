"""Helpers for casting from environment variable string to other types."""

from __future__ import annotations

import json
import sys
from typing import Callable, Dict, Type, Union, get_args, get_origin

from .errors import UnsupportedTypeError

if sys.version_info >= (3, 10):
    from types import NoneType, UnionType
else:
    NoneType = type(None)
    UnionType = Union


__all__ = ["get_caster", "EnvVarCaster"]

SupportedType = Union[int, float, str, bool, dict, Dict]

_TRUE_VALUES = {"true", "yes", "on", "y", "1"}
_FALSE_VALUES = {"false", "no", "off", "n", "0"}


def _str_to_bool(value: str) -> bool:
    """Determine if string value is truthy."""
    value = value.lower()

    if value in _TRUE_VALUES:
        return True
    elif value in _FALSE_VALUES:
        return False

    raise ValueError(value)


def _str_to_dict(value: str) -> dict:
    """Convert string (JSON) to dictionary."""
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError:
        raise ValueError(value)


EnvVarCaster = Callable[[str], SupportedType]

_PRIMITIVES_CASTERS: dict[Type[SupportedType], EnvVarCaster] = {
    int: int,
    float: float,
    str: str,
    bool: _str_to_bool,
    dict: _str_to_dict,
    Dict: _str_to_dict,
}


def get_caster(type_: Type) -> EnvVarCaster:
    """Get caster for a given type."""
    if _is_single_nullable(type_):
        type_ = _reduce_from_nullable(type_)

    caster = _PRIMITIVES_CASTERS.get(type_)
    if caster is None:
        raise UnsupportedTypeError(type_)

    return caster


def _is_single_nullable(tp: Type) -> bool:
    origin_type = get_origin(tp)
    is_union = origin_type is UnionType or origin_type is Union

    if not is_union:
        return False

    type_args = get_args(tp)
    return len(type_args) == 2 and NoneType in type_args


def _reduce_from_nullable(tp: Type):
    type_args = get_args(tp)

    if len(type_args) != 2:
        raise TypeError("Type {} is not nullable".format(tp))

    if type_args[0] is NoneType:
        return type_args[1]
    elif type_args[1] is NoneType:
        return type_args[0]
    else:
        raise TypeError("Type {} is not nullable".format(tp))
