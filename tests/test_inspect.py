import typing as t
from enum import Enum
from unittest.mock import patch

import pytest

from envarify import inspect

from .const import PYTHON_IS_NEW


def test_type_inspector_init_ok():
    ti = inspect.TypeInspector(t.Dict[str, int])
    assert ti.type == dict[str, int]
    assert ti.origin_type == dict
    assert ti.type_args == (str, int)


def test_type_inspector_init_ignore_nullable_ok():
    ti = inspect.TypeInspector(t.Optional[int], ignore_nullable=True)
    assert ti.type is int
    assert ti.origin_type is int
    assert ti.type_args is tuple()


@pytest.mark.parametrize(
    "type_, expected",
    (
        [
            (t.Optional[int], True),
            (t.Optional[t.List[int]], True),
            (t.Union[None, str], True),
            (t.Union[str, int, None], False),
            (int, False),
        ]
        + (
            [
                (int | None, True),
                (None | str, True),
                (str | int | None, False),
            ]
            if PYTHON_IS_NEW
            else []
        )
    ),
)
def test_type_inspector_is_single_nullable_ok(type_, expected):
    assert inspect.TypeInspector(type_).is_single_nullable() is expected


def test_type_inspector_is_string_enum():
    class MockStrEnum(str, Enum): ...

    assert inspect.TypeInspector(MockStrEnum).is_string_enum()


@pytest.mark.parametrize(
    "type_, expected",
    [
        (t.Dict, True),
        (dict, True),
        (set, False),
    ],
)
def test_type_inspector_is_dict_ok(type_, expected):
    assert inspect.TypeInspector(type_).is_dict() is expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (list, True),
        (t.List, True),
        (set, True),
        (tuple, True),
        (str, False),
    ],
)
def test_type_inspector_is_sequence_ok(type_, expected):
    assert inspect.TypeInspector(type_).is_sequence() is expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (t.Optional[int], int),
        (t.Union[None, str], str),
    ],
)
def test_type_inspector_extract_from_nullable_ok(type_, expected):
    assert inspect.TypeInspector(type_).extract_from_nullable() == expected


def test_type_inspector_extract_from_nullable_error():
    with pytest.raises(TypeError):
        inspect.TypeInspector(int).extract_from_nullable()

    with pytest.raises(TypeError):
        inspect.TypeInspector(int | str).extract_from_nullable()


@pytest.mark.parametrize(
    "type_, expected",
    [
        (list[int], int),
        (set[tuple[int]], tuple[int]),
    ],
)
def test_type_inspector_extract_inner_value_type_ok(type_, expected):
    assert inspect.TypeInspector(type_).extract_inner_value_type() == expected


def test_type_inspector_extract_inner_value_type_error():
    with pytest.raises(inspect.UnsupportedTypeError):
        inspect.TypeInspector(tuple[int, str]).extract_inner_value_type()
