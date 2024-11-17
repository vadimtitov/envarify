"""Host type definitions."""

from __future__ import annotations

import re


class SecretString:
    """Secret string.

    - Access a secret value only using explicit reveal() method
    - Erase secret value from memory before object destruction
    """

    def __init__(self, value: str) -> None:
        """Initialize."""
        self.__value = bytearray(value, "utf-8")

    def reveal(self) -> str:
        """Return the actual secret value."""
        return self.__value.decode("utf-8")

    def erase(self) -> None:
        """Erase secret value from memory."""
        for i in range(len(self.__value)):
            self.__value[i] = 0  # Overwrite each byte with null byte

    def __str__(self) -> str:
        """Return masked representation."""
        return "******"

    def __repr__(self) -> str:
        """Return masked representation."""
        return "'******'"

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if isinstance(other, SecretString):
            return self.__value == other.__value
        return False

    def __hash__(self) -> int:
        """Return object hash."""
        return hash(self.__value.decode("utf-8"))

    def __del__(self) -> None:
        """Erase value from memory before object is destroyed."""
        self.erase()


def _get_url_regex(protocols: list[str] | None = None) -> re.Pattern:
    protocols_regex = "|".join(protocols) if protocols else "[a-z]+"

    return re.compile(
        r"^((?:{})://)".format(protocols_regex)
        + r"((([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})|"  # Match protocols  # Match domain names
        r"(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b))"  # Match IPv4 addresses
        r"(:[0-9]{1,5})?"  # Optional port
        r"(/.*)?$",  # Optional path
        re.IGNORECASE,
    )


class Url(str):
    """
    Base class for validating a URL based on a regular expression.

    Attributes:
        _regex: Compiled regular expression used for validation.
        _name: Descriptive name of the URL type.
    """

    _regex: re.Pattern = _get_url_regex()
    _name: str = "URL"

    def __new__(cls, value: str) -> Url:
        """Create as string but validate first."""
        if not cls._regex.match(value):
            raise ValueError("Invalid {}: {}".format(cls._name, value))
        return str.__new__(cls, value)


class HttpUrl(Url):
    """Validates HTTP URL."""

    _regex = _get_url_regex(["http"])
    _name = "HTTP URL"


class HttpsUrl(Url):
    """Validates HTTPS URL."""

    _regex = _get_url_regex(["https"])
    _name = "HTTPS URL"


class AnyHttpUrl(Url):
    """Validates either HTTP or HTTPS URL."""

    _regex = _get_url_regex(["http", "https"])
    _name = "HTTP or HTTPS URL"
