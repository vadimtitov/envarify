from unittest.mock import patch

import pytest

import envarify
from envarify import BaseConfig, EnvVar, MissingEnvVarError


@patch.dict(
    envarify.os.environ,
    {
        "TEST_INT": "666",
        "TEST_FLOAT": "3.14",
        "TEST_STR": "Hello",
        "TEST_BOOL": "true",
    },
)
def test_simple_case():

    class MyConfig(BaseConfig):
        test_int: int = EnvVar("TEST_INT")
        test_float: float = EnvVar("TEST_FLOAT")
        test_str: str = EnvVar("TEST_STR")
        test_bool: bool = EnvVar("TEST_BOOL")

    config = MyConfig.fromenv()
    assert config.test_int == 666
    assert config.test_float == 3.14
    assert config.test_str == "Hello"
    assert config.test_bool == True


def test_missing_envvar_error_raised():
    class MyConfig(BaseConfig):
        x: int = EnvVar("SOME_NOT_EXISTING_ENVVAR")

    with pytest.raises(MissingEnvVarError):
        MyConfig.fromenv()
