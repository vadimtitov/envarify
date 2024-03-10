import typing as t
from unittest.mock import patch

import pytest

from envarify import UnsupportedTypeError, cast

from .const import PYTHON_IS_NEW


@pytest.mark.parametrize(
    "given, expected",
    [
        ("true", True),
        ("Yes", True),
        ("on", True),
        ("y", True),
        ("1", True),
        ("false", False),
        ("NO", False),
        ("OFF", False),
        ("n", False),
        ("0", False),
    ],
)
def test_str_to_bool_ok(given, expected):
    assert cast._str_to_bool(given) is expected


def test_str_to_bool_raises_error():
    with pytest.raises(ValueError):
        cast._str_to_bool("try")


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, int),
        (t.Optional[int], int),
        (bool, cast._str_to_bool),
        (t.Union[str, None], str),
        (float, float),
    ]
    + (
        [
            (int | None, int),
            (None | str, str),
        ]
        if PYTHON_IS_NEW
        else []
    ),
)
def test_get_caster_ok(type_, expected):
    assert cast.get_caster(type_) == expected


def test_get_caster_raises_error():
    class SomeCringeType:
        pass

    with pytest.raises(UnsupportedTypeError):
        cast.get_caster(SomeCringeType)


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
            [(int | None, True), (None | str, True), (str | int | None, False)]
            if PYTHON_IS_NEW
            else []
        )
    ),
)
def test_is_single_nullable_ok(type_, expected):
    assert cast._is_single_nullable(type_) is expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (t.Optional[int], int),
        (t.Union[None, str], str),
    ],
)
def test_reduce_from_nullable_ok(type_, expected):
    assert cast._reduce_from_nullable(type_) is expected


def test_reduce_from_nullable_raises_erro():
    with pytest.raises(TypeError):
        cast._reduce_from_nullable(int)

    with pytest.raises(TypeError):
        cast._reduce_from_nullable(int | str)
