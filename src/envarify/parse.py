"""Helpers for parsing from environment variable string to other types."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable, Type, TypeVar

from .errors import UnsupportedTypeError
from .inspect import SupportedType, TypeInspector
from .types import AnyHttpUrl, HttpsUrl, HttpUrl, SecretString, Url

if TYPE_CHECKING:
    from .envarify import _EnvVarSpec


__all__ = ["get_parser", "EnvVarParser"]


_T = TypeVar("_T")
EnvVarParser = Callable[[str], _T]


def get_parser(type_: Type, spec: _EnvVarSpec[SupportedType]) -> EnvVarParser[SupportedType]:
    """Get parser for a given type."""
    ti = TypeInspector(type_, ignore_nullable=True)

    # primitive
    parser = _PARSERS.get(ti.type)
    if parser is not None:
        return parser

    # string enum
    if ti.is_string_enum():
        return type_

    # dictionary
    if ti.is_dict():
        return _str_to_dict

    # sequence
    if ti.is_sequence():
        parser = _get_sequence_parser(
            sequence_type=ti.origin_type,
            value_type=ti.extract_inner_value_type(),
            delimiter=spec.delimiter,
        )
        if parser is not None:
            return parser

    raise UnsupportedTypeError(type_)


def _str_to_bool(value: str | bool) -> bool:
    """Determine if string value is truthy."""
    if isinstance(value, bool):
        return value

    value = value.lower()

    if value in _TRUE_VALUES:
        return True
    elif value in _FALSE_VALUES:
        return False

    raise ValueError("Cannot convert to bool: " + value)


def _str_to_dict(value: str | dict) -> dict:
    """Convert string (JSON) to dictionary."""
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)  # type: ignore
    except json.decoder.JSONDecodeError:
        raise ValueError("Cannot convert to dictionary: " + value)


def _get_sequence_parser(sequence_type: Type, value_type: Type, delimiter: str) -> Callable | None:
    try:
        value_parser = _PARSERS[value_type]
    except KeyError:
        return None

    def parser(sequence: str) -> Any:
        return sequence_type(value_parser(value) for value in sequence.split(delimiter))

    return parser


_PARSERS: dict[Type[SupportedType], EnvVarParser[SupportedType]] = {
    int: int,
    float: float,
    str: str,
    bool: _str_to_bool,
    datetime: datetime.fromisoformat,
    date: date.fromisoformat,
    SecretString: SecretString,
    AnyHttpUrl: AnyHttpUrl,
    HttpUrl: HttpUrl,
    HttpsUrl: HttpsUrl,
    Url: Url,
}

_TRUE_VALUES = {"true", "yes", "on", "y", "1"}
_FALSE_VALUES = {"false", "no", "off", "n", "0"}
