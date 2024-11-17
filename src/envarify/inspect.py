"""Type inspection helper."""

import sys
from datetime import date, datetime
from enum import Enum
from typing import Type, Union, get_args, get_origin

if sys.version_info >= (3, 10):
    from types import NoneType, UnionType
else:
    NoneType = type(None)
    UnionType = Union

from .errors import UnsupportedTypeError
from .types import AnyHttpUrl, HttpsUrl, HttpUrl, SecretString, Url

SupportedType = Union[
    int,
    float,
    str,
    bool,
    dict,
    list,
    set,
    tuple,
    datetime,
    date,
    Enum,
    AnyHttpUrl,
    HttpsUrl,
    HttpUrl,
    SecretString,
    Url,
]


class UndefinedType:
    """Undefined type.

    Needed since None is a valid default value in EnvVar specification.
    """


Undefined = UndefinedType()


class TypeInspector:
    """Helper class for type inspection and extraction."""

    def __init__(self, type_: Type, ignore_nullable: bool = False) -> None:
        """Initialize."""
        if ignore_nullable and (ti := TypeInspector(type_)):
            if ti.is_single_nullable():
                type_ = ti.extract_from_nullable()

        origin, args = get_origin(type_), get_args(type_)
        if origin is None:
            origin = type_

        try:
            self.type = origin[args] if args else origin
        except TypeError:
            self.type = type_
        self.origin_type = origin
        self.type_args = args

    def is_single_nullable(self) -> bool:
        """Check if type is a union of strictly one type and None."""
        is_union = self.origin_type is UnionType or self.origin_type is Union
        if not is_union:
            return False
        return len(self.type_args) == 2 and NoneType in self.type_args

    def is_string_enum(self) -> bool:
        """Check if type is a string enum."""
        return issubclass(self.origin_type, str) and issubclass(self.origin_type, Enum)

    def is_dict(self) -> bool:
        """Check if type is a dictionary."""
        return self.origin_type is dict

    def is_sequence(self) -> bool:
        """Check if type is list. set or tuple."""
        return self.origin_type is list or self.origin_type is set or self.origin_type is tuple

    def extract_from_nullable(self) -> Type:
        """Extract base type from nullable/optional object."""
        if len(self.type_args) != 2:
            raise TypeError("Type {} is not nullable".format(self.type))

        if self.type_args[0] is NoneType:
            return self.type_args[1]  # type: ignore
        elif self.type_args[1] is NoneType:
            return self.type_args[0]  # type: ignore
        else:
            raise TypeError("Type {} is not nullable".format(self.type))

    def extract_inner_value_type(self) -> Type:
        """Extract inner value from type e.g. T from list[T]."""
        if len(self.type_args) > 1:
            raise UnsupportedTypeError(self.type)

        return self.type_args[0] if self.type_args else str
