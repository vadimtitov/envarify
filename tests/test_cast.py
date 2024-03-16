import typing as t
from unittest.mock import patch

import pytest

from envarify import UnsupportedTypeError, parse

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
    assert parse._str_to_bool(given) is expected


def test_str_to_bool_raises_error():
    with pytest.raises(ValueError):
        parse._str_to_bool("try")


def test_str_to_dict():
    sample_json = '{"A": 1, "B": "b", "C": {"D": true}}'
    expected = {"A": 1, "B": "b", "C": {"D": True}}
    assert parse._str_to_dict(sample_json) == expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, int),
        (t.Optional[int], int),
        (bool, parse._str_to_bool),
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
def test_get_parser_ok(type_, expected):
    assert parse.get_parser(type_) == expected


def test_get_parser_raises_error():
    class SomeCringeType:
        pass

    with pytest.raises(UnsupportedTypeError):
        parse.get_parser(SomeCringeType)


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
    assert parse._is_single_nullable(type_) is expected


@pytest.mark.parametrize(
    "type_, expected",
    [
        (t.Optional[int], int),
        (t.Union[None, str], str),
    ],
)
def test_reduce_from_nullable_ok(type_, expected):
    assert parse._reduce_from_nullable(type_) is expected


def test_reduce_from_nullable_raises_erro():
    with pytest.raises(TypeError):
        parse._reduce_from_nullable(int)

    with pytest.raises(TypeError):
        parse._reduce_from_nullable(int | str)
