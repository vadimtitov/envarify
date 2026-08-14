"""Tests for configs defined in modules using `from __future__ import annotations` (PEP 563)."""

from __future__ import annotations

import typing as t
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

import envarify
from envarify import AnnotationError, BaseConfig, EnvVar

from .future_base import FutureBaseConfig

if TYPE_CHECKING:
    from decimal import Decimal


# Configs are defined at module level because PEP 563 string annotations
# are evaluated against module globals and cannot see function locals.


class ScalarConfig(BaseConfig):
    test_int: int = EnvVar("TEST_FUTURE_INT")
    test_str: str = EnvVar("TEST_FUTURE_STR")
    test_opt: t.Optional[float] = EnvVar("TEST_FUTURE_INT")
    test_default: int | None = EnvVar(default=None)


class NestedConfig(BaseConfig):
    scalars: ScalarConfig
    test_bool: bool = EnvVar("TEST_FUTURE_BOOL")


class InheritedConfig(FutureBaseConfig):
    test_int: int = EnvVar("TEST_FUTURE_INT")


class UnresolvableConfig(BaseConfig):
    test_decimal: Decimal = EnvVar("TEST_FUTURE_INT")


TEST_ENVIRON = {
    "TEST_FUTURE_INT": "666",
    "TEST_FUTURE_STR": "Hello",
    "TEST_FUTURE_BOOL": "true",
    "TEST_FUTURE_SECRET": "secret",
}


@patch.dict(envarify.envarify.os.environ, TEST_ENVIRON)
def test_base_config_fromenv_scalar_ok():
    config = ScalarConfig.fromenv()
    assert config.test_int == 666
    assert config.test_str == "Hello"
    assert config.test_opt == 666.0
    assert config.test_default is None


@patch.dict(envarify.envarify.os.environ, TEST_ENVIRON)
def test_base_config_fromenv_nested_ok():
    config = NestedConfig.fromenv()
    assert config.test_bool == True
    assert config.scalars.test_int == 666
    assert config.scalars.test_str == "Hello"


@patch.dict(envarify.envarify.os.environ, TEST_ENVIRON)
def test_base_config_fromenv_cross_module_inheritance_ok():
    config = InheritedConfig.fromenv()
    assert config.test_int == 666
    assert config.base_secret.reveal() == "secret"


@patch.dict(envarify.envarify.os.environ, TEST_ENVIRON)
def test_base_config_fromenv_unresolvable_annotation_error_raised():
    with pytest.raises(AnnotationError, match="Decimal"):
        UnresolvableConfig.fromenv()
