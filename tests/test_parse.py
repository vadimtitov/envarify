import typing as t
from enum import Enum
from unittest.mock import patch

import pytest

from envarify import EnvVar, UnsupportedTypeError, parse

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
        (True, True),
        (False, False),
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
    assert parse._str_to_dict(expected) == expected


class MockStrEnum(str, Enum): ...


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, int),
        (t.Optional[int], int),
        (bool, parse._str_to_bool),
        (t.Union[str, None], str),
        (float, float),
        (dict, parse._str_to_dict),
        (MockStrEnum, MockStrEnum),
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
    assert parse.get_parser(type_, EnvVar()) == expected


@patch("envarify.parse._get_sequence_parser", return_value="X")
def test_get_parser_returns_sequence_ok(mock_get_sequence_parser):
    assert parse.get_parser(list[int], EnvVar(delimiter="|")) == "X"
    mock_get_sequence_parser.assert_called_once_with(
        sequence_type=list,
        value_type=int,
        delimiter="|",
    )


def test_get_parser_raises_error():
    class SomeCringeType:
        pass

    with pytest.raises(UnsupportedTypeError):
        parse.get_parser(SomeCringeType, EnvVar())


@pytest.mark.parametrize(
    "outer, inner, value, expected",
    [
        (list, int, "1,2,3", [1, 2, 3]),
        (tuple, int, "1,2,3", (1, 2, 3)),
        (set, int, "1,2,3", {1, 2, 3}),
        (list, bool, "1,0,1", [True, False, True]),
    ],
)
def test_get_sequence_parser_ok(outer, inner, value, expected):
    assert parse._get_sequence_parser(outer, inner, ",")(value) == expected
