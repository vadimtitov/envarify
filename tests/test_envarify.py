import typing as t
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Union
from unittest.mock import patch

import pytest

import envarify
from envarify import (
    AnnotationError,
    BaseConfig,
    EnvVar,
    MissingEnvVarsError,
    SecretString,
    UnsupportedTypeError,
    Url,
)
from envarify.envarify import Undefined, _EnvVarSource

from .const import PYTHON_IS_NEW


class MyConfig(BaseConfig):
    x: int
    y: str
    d: str = EnvVar("D", default="default")


def test_base_config_init_ok():
    config = MyConfig(x=1, y="2")
    assert config.x == 1
    assert config.y == "2"
    assert config.d == "default"


def test_base_config_init_ok_default_passed():
    config = MyConfig(x=1, y="2", d="passed")
    assert config.x == 1
    assert config.y == "2"
    assert config.d == "passed"


def test_base_config_init_raises_error():
    with pytest.raises(TypeError):
        MyConfig(z=1)


def test_base_config_repr_ok():
    assert MyConfig(x=1, y="2").__repr__() == "MyConfig(x=1, y='2', d='default')"


class TestStrEnum(str, Enum):

    TEST_VALUE = "TEST_STR_ENUM_VALUE"


@patch.dict(
    envarify.envarify.os.environ,
    {
        "TEST_INT": "666",
        "TEST_FLOAT": "3.14",
        "TEST_STR": "Hello",
        "TEST_BOOL": "true",
        "TEST_SET": "1|2|3",
        "TEST_CUSTOM": "a,b,c",
        "TEST_SECRET": "secret",
        "TEST_URL": "ws://example.com",
        "TEST_ISO_DATE": "2024-04-13",
        "TEST_ISO_DATETIME": "2024-11-17T12:34:56.789123",
        "TEST_STR_ENUM": "TEST_STR_ENUM_VALUE",
    },
)
def test_base_config_fromenv_ok():

    class PrimitivesConfig(BaseConfig):
        test_int: int = EnvVar("TEST_INT")
        test_float: float = EnvVar("TEST_FLOAT")
        test_str: str = EnvVar("TEST_STR")
        test_str_default: str = EnvVar("TEST_STR", default="default")
        test_bool: bool = EnvVar("TEST_BOOL")
        test_bool_default: bool = EnvVar("FAKE_BOOL", default=False)
        test_secret: SecretString = EnvVar("TEST_SECRET")
        test_url: Url = EnvVar("TEST_URL")
        test_iso_date: date = EnvVar("TEST_ISO_DATE")
        test_iso_datetime: datetime = EnvVar("TEST_ISO_DATETIME")
        test_str_enum: TestStrEnum = EnvVar("TEST_STR_ENUM")

    class MyConfig(BaseConfig):
        primitives: PrimitivesConfig
        test_set: t.Set[int] = EnvVar("TEST_SET", delimiter="|")
        test_custom: t.List[str] = EnvVar("TEST_CUSTOM", parse=lambda v: v.split(","))

        def custom_method(self) -> int:
            return self.primitives.test_int * 10

        @property
        def custom_property(self) -> str:
            return "Custom " + self.primitives.test_str

    config = MyConfig.fromenv()
    assert config.primitives.test_int == 666
    assert config.primitives.test_float == 3.14
    assert config.primitives.test_str == "Hello"
    assert config.primitives.test_str_default == "Hello"
    assert config.primitives.test_bool == True
    assert config.primitives.test_bool_default == False
    assert str(config.primitives.test_secret) == "******"
    assert config.primitives.test_secret.reveal() == "secret"
    assert config.primitives.test_url == "ws://example.com"
    assert config.primitives.test_iso_datetime == datetime(2024, 11, 17, 12, 34, 56, 789123)
    assert config.primitives.test_iso_date == date(2024, 4, 13)
    assert config.primitives.test_str_enum is TestStrEnum.TEST_VALUE

    assert config.test_set == {1, 2, 3}
    assert config.test_custom == ["a", "b", "c"]
    assert config.custom_method() == 6660
    assert config.custom_property == "Custom Hello"


@patch.dict(envarify.envarify.os.environ, {"XXX": "666"})
def test_base_config_fromenv_nullable_arguments_ok():
    if PYTHON_IS_NEW:

        class MyConfig(BaseConfig):
            test_opt: t.Optional[int] = EnvVar("XXX")
            test_union: t.Union[float, None] = EnvVar("XXX")
            test_default: int | None = EnvVar(default=None)

    else:

        class MyConfig(BaseConfig):
            test_opt: t.Optional[int] = EnvVar("XXX")
            test_union: t.Union[float, None] = EnvVar("XXX")
            test_default: t.Optional[int] = EnvVar(default=None)

    config = MyConfig.fromenv()
    assert config.test_opt == 666
    assert config.test_union == 666.0
    assert config.test_default is None


def test_base_config_fromenv_envvar_error_raised():
    class ConfigInside(BaseConfig):
        y: str = EnvVar("SOME_SUPER_UNLICKELY_ENVVAR")

    class MyConfig(BaseConfig):
        y: ConfigInside
        x: int = EnvVar("SOME_NOT_EXISTING_ENVVAR")

    with pytest.raises(MissingEnvVarsError) as e:
        MyConfig.fromenv()
        assert e.env_vars == ["SOME_NOT_EXISTING_ENVVAR", "SOME_SUPER_UNLICKELY_ENVVAR"]


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
        y: str = EnvVar(parse=test_func)

    assert MyConfig._envvars() == [
        _EnvVarSource(attr="x", name="TEST_X", default=5, parse=int),
        _EnvVarSource(attr="y", name="y", default=Undefined, parse=test_func),
    ]


def test_base_config_equal():

    class MyConfig(BaseConfig):
        x: int
        y: str

    assert MyConfig(x=1, y="2") == MyConfig(y="2", x=1)
    assert MyConfig(x=1, y="3") != MyConfig(y="2", x=1)


def test_base_config_hash():

    class MyConfig(BaseConfig):
        x: int
        y: str

    class NotMyConfig(BaseConfig):
        x: int
        y: str

    assert hash(MyConfig(x=1, y="2")) == hash(MyConfig(y="2", x=1))
    assert MyConfig(x=1, y="2") in {MyConfig(y="2", x=1)}
    assert MyConfig(x=1, y="2") not in {NotMyConfig(y="2", x=1)}
    assert MyConfig(x=1, y="3") not in {MyConfig(y="2", x=1)}


@patch.dict(envarify.envarify.os.environ, {"X": "25"})
def test_envvar_exists_ok():
    env_var = _EnvVarSource("x", "X", str)
    assert env_var.exists()


@patch.dict(envarify.envarify.os.environ, {})
def test_envvar_exists_not():
    env_var = _EnvVarSource("x", "X", str)
    assert not env_var.exists()


@patch("envarify.envarify._EnvVarSource.exists", return_value=True)
def test_envvar_has_value_ok(mock):
    env_var = _EnvVarSource("x", "X", str)
    assert env_var.has_value()


@patch("envarify.envarify._EnvVarSource.exists", return_value=False)
def test_envvar_has_value_ok_default(mock):
    env_var = _EnvVarSource("", "", str, default="x")
    assert env_var.has_value()


@patch("envarify.envarify._EnvVarSource.exists", return_value=False)
def test_envvar_has_value_ok_not(mock):
    env_var = _EnvVarSource("", "", str)
    assert not env_var.has_value()
