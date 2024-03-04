"""Helpers for casting from environment variable string to other types."""

from typing import Callable, TypeVar, Union, Generic

__all__ = ["get_caster", "EnvvarCaster"]

T = TypeVar("T", bound=Union[int, float, str, bool])

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


EnvvarCaster = Callable[[str], T]

_CASTERS: dict[T, EnvvarCaster] = {
    int: int,
    float: float,
    str: str,
    bool: _str_to_bool,
}


def get_caster(type_: T) -> EnvvarCaster:
    """Get caster for a given type."""
    return _CASTERS[type_]
