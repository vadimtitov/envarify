import typing as t
from dataclasses import dataclass
from typing import Optional, Union
from unittest.mock import patch

import pytest

import envarify
from envarify import AnnotationError, BaseConfig, EnvVar, MissingEnvVarsError, UnsupportedTypeError
from envarify.envarify import _EnvVar

from .const import PYTHON_IS_NEW


class MyConfig(BaseConfig):
    x: int
    y: str


def test_base_config_init_ok():
    config = MyConfig(x=1, y="2")
    assert config.x == 1
    assert config.y == "2"


def test_base_config_init_raises_error():
    with pytest.raises(TypeError):
        MyConfig(z=1)


def test_base_config_repr_ok():
    assert MyConfig(x=1, y="2").__repr__() == "MyConfig(x=1, y='2')"


@patch.dict(
    envarify.envarify.os.environ,
    {
        "TEST_INT": "666",
        "TEST_FLOAT": "3.14",
        "TEST_STR": "Hello",
        "TEST_BOOL": "true",
        "TEST_CUSTOM": "a,b,c",
    },
)
def test_base_config_fromenv_ok():

    class MyConfig(BaseConfig):
        test_int: int = EnvVar("TEST_INT")
        test_float: float = EnvVar("TEST_FLOAT")
        test_str: str = EnvVar("TEST_STR")
        test_bool: bool = EnvVar("TEST_BOOL")
        test_custom: t.List[str] = EnvVar("TEST_CUSTOM", cast=lambda v: v.split(","))

    config = MyConfig.fromenv()
    assert config.test_int == 666
    assert config.test_float == 3.14
    assert config.test_str == "Hello"
    assert config.test_bool == True
    assert config.test_custom == ["a", "b", "c"]


@patch.dict(envarify.envarify.os.environ, {"XXX": "666"})
def test_base_config_fromenv_nullable_arguments_ok():
    if PYTHON_IS_NEW:

        class MyConfig(BaseConfig):
            test_opt: t.Optional[int] = EnvVar("XXX")
            test_union: t.Union[float, None] = EnvVar("XXX")
            test_default: int | None = EnvVar(default=45)

    else:

        class MyConfig(BaseConfig):
            test_opt: t.Optional[int] = EnvVar("XXX")
            test_union: t.Union[float, None] = EnvVar("XXX")
            test_default: t.Optional[int] = EnvVar(default=45)

    config = MyConfig.fromenv()
    assert config.test_opt == 666
    assert config.test_union == 666.0
    assert config.test_default == 45


def test_base_config_fromenv_envvar_error_raised():
    class MyConfig(BaseConfig):
        x: int = EnvVar("SOME_NOT_EXISTING_ENVVAR")

    with pytest.raises(MissingEnvVarsError):
        MyConfig.fromenv()


def test_base_config_fromenv_unsupported_type_error_raised():
    class SomeCringeType:
        pass

    class MyConfig(BaseConfig):
        TEST: SomeCringeType

    with pytest.raises(UnsupportedTypeError):
        MyConfig.fromenv()


def test_base_config_fromenv_annotation_error_raised():
    class MyConfig(BaseConfig):
        pass

    with pytest.raises(AnnotationError):
        MyConfig.fromenv()


def test_base_config_envvars_ok():

    test_func = lambda x: x

    class MyConfig(BaseConfig):
        x: int = EnvVar("TEST_X", default=5)
        y: str = EnvVar(cast=test_func)

    assert MyConfig._envvars() == [
        _EnvVar(attr="x", name="TEST_X", default=5, cast=int),
        _EnvVar(attr="y", name="y", default=None, cast=test_func),
    ]


@patch.dict(envarify.envarify.os.environ, {"X": "25"})
def test_envvar_exists_ok():
    env_var = _EnvVar("x", "X", str)
    assert env_var.exists()


@patch.dict(envarify.envarify.os.environ, {})
def test_envvar_exists_not():
    env_var = _EnvVar("x", "X", str)
    assert not env_var.exists()


@patch("envarify.envarify._EnvVar.exists", return_value=True)
def test_envvar_has_value_ok(mock):
    env_var = _EnvVar("x", "X", str)
    assert env_var.has_value()


@patch("envarify.envarify._EnvVar.exists", return_value=False)
def test_envvar_has_value_ok_default(mock):
    env_var = _EnvVar("", "", str, default="x")
    assert env_var.has_value()


@patch("envarify.envarify._EnvVar.exists", return_value=False)
def test_envvar_has_value_ok_not(mock):
    env_var = _EnvVar("", "", str)
    assert not env_var.has_value()


def test_envvar_value():
    pass
