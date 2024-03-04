"""Envarify implementation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterator

from .cast import EnvvarCaster, get_caster

__all__ = ["BaseConfig", "Envvar", "MissingEnvvarError"]


class MissingEnvvarError(Exception):
    """Missing environment variables error."""

    pass


@dataclass(frozen=True)
class Envvar:
    """Environment variable spec for package API."""

    name: str | None = None
    default: str | None = None
    cast: EnvvarCaster | None = None


@dataclass(frozen=True)
class _Envvar:
    """Environment variable representation."""

    attr: str
    name: str
    cast: EnvvarCaster
    default: str | None = None

    def exists(self) -> bool:
        """Check if this environment variable exists."""
        return self.name in os.environ

    def has_value(self) -> bool:
        """Check if this environment variable has value."""
        return self.default is not None or self.exists()

    def value(self) -> Any | None:
        """Check if this environment variable has value."""
        if self.has_value():
            value = os.environ.get(self.name, default=self.default)
            return self.cast(value)  # type: ignore
        return None


class BaseConfig:
    """Base config class."""

    def __init__(self, **kwargs) -> None:
        """Initialize this object."""  # TODO
        for key in self.__annotations__:
            if key not in kwargs:
                raise TypeError(key)
            setattr(self, key, kwargs[key])

    def __repr__(self) -> str:
        """Return representation."""
        return "{name}({attributes})".format(
            name=self.__class__.__name__,
            attributes=", ".join(
                "{key}={value}".format(key=key, value=getattr(self, key))
                for key in self.__annotations__
            ),
        )

    @classmethod
    def fromenv(cls) -> BaseConfig:
        """Initialize this object from environment variables."""
        cls._validate()
        return cls(**{v.attr: v.value() for v in cls._envvars()})

    @classmethod
    def _validate(cls) -> None:
        """Validate environment variables."""
        missing_envvars = [e.name for e in cls._envvars() if not e.has_value()]

        if missing_envvars:
            raise MissingEnvvarError(", ".join(missing_envvars))

    @classmethod
    def _envvars(cls) -> Iterator[_Envvar]:
        """Yield over all environment variables."""
        for key, type_ in cls.__annotations__.items():
            spec: Envvar | None = cls.__dict__.get(key)

            if isinstance(spec, Envvar):
                yield _Envvar(
                    attr=key,
                    name=spec.name or key,
                    default=spec.default,
                    cast=get_caster(type_),
                )
            elif spec is None:
                yield _Envvar(
                    attr=key,
                    name=key,
                    cast=get_caster(type_),
                )
            else:
                raise TypeError(spec)
