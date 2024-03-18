"""Helpers for parsing from environment variable string to other types."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable, Type

from .errors import UnsupportedTypeError
from .inspect import SupportedType, TypeInspector

if TYPE_CHECKING:
    from .envarify import EnvVar


__all__ = ["get_parser", "EnvVarParser"]


EnvVarParser = Callable[[str], SupportedType]


def get_parser(type_: Type, spec: EnvVar) -> EnvVarParser:
    """Get parser for a given type."""
    ti = TypeInspector(type_, ignore_nullable=True)

    # primitive
    parser = _PRIMITIVE_PARSERS.get(ti.type)
    if parser is not None:
        return parser

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


def _str_to_bool(value: str) -> bool:
    """Determine if string value is truthy."""
    value = value.lower()

    if value in _TRUE_VALUES:
        return True
    elif value in _FALSE_VALUES:
        return False

    raise ValueError("Cannot convert to bool: " + value)


def _str_to_dict(value: str) -> dict:
    """Convert string (JSON) to dictionary."""
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError:
        raise ValueError("Cannot convert to dictionary: " + value)


def _get_sequence_parser(sequence_type: Type, value_type: Type, delimiter: str) -> Callable | None:
    try:
        value_parser = _PRIMITIVE_PARSERS[value_type]
    except KeyError:
        return None

    def parser(sequence: str):
        return sequence_type(value_parser(value) for value in sequence.split(delimiter))

    return parser


_PRIMITIVE_PARSERS: dict[Type[SupportedType], EnvVarParser] = {
    int: int,
    float: float,
    str: str,
    bool: _str_to_bool,
}
_TRUE_VALUES = {"true", "yes", "on", "y", "1"}
_FALSE_VALUES = {"false", "no", "off", "n", "0"}
