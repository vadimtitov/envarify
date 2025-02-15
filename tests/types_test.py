"""File to run agains mypy to verify that type checks work as expected."""

from envarify import BaseConfig, EnvVar, SecretString


class CustomType:

    def __init__(self, value: str):
        self.value = value


class MyConfig(BaseConfig):

    timeout_s: float = EnvVar("TIMEOUT_S")
    api_key: SecretString = EnvVar("API_KEY")
    allowed_ids: set[int] = EnvVar("ALLOWED_IDS")
    enable_feature: bool = EnvVar("ENABLE_FEATURE", default=False)
    optional_arg: str | None = EnvVar("OPTIONAL_ARG", default=None)
    custom_type: CustomType = EnvVar("CUSTOM_TYPE", default=CustomType("lol"))
    custom_type_2: CustomType = EnvVar("CUSTOM_TYPE_2", parse=lambda x: CustomType(x))
