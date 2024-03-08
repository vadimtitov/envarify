"""Helpers for casting from environment variable string to other types."""

from typing import Callable, Generic, TypeVar, Union

from .errors import UnsupportedTypeError

__all__ = ["get_caster", "EnvVarCaster"]

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


EnvVarCaster = Callable[[str], T]

_CASTERS: dict[T, EnvVarCaster] = {
    int: int,
    float: float,
    str: str,
    bool: _str_to_bool,
}


def get_caster(type_: T) -> EnvVarCaster:
    """Get caster for a given type."""
    caster = _CASTERS.get(type_)
    if caster is None:
        raise UnsupportedTypeError(type_)

    return caster
