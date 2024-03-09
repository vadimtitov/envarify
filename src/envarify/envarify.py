"""Envarify implementation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache
from typing import Any

from .cast import EnvVarCaster, get_caster
from .errors import AnnotationError, MissingEnvVarsError


@dataclass(frozen=True)
class EnvVar:
    """Environment variable spec for package API."""

    name: str | None = None
    default: str | None = None
    cast: EnvVarCaster | None = None


class BaseConfig:
    """Base config class."""

    def __init__(self, **kwargs) -> None:
        """Initialize this object."""
        for key, value in kwargs.items():
            if key not in self._properties():
                raise TypeError(f"Unexpected keyword argument '{key}'")
            setattr(self, key, value)

    def __repr__(self) -> str:
        """Return representation."""
        return "{name}({attributes})".format(
            name=self.__class__.__name__,
            attributes=", ".join(
                "{key}={value}".format(key=key, value=getattr(self, key))
                for key in self._annotations()
            ),
        )

    @classmethod
    def fromenv(cls) -> BaseConfig:
        """Initialize this object from environment variables.

        Returns:
            BaseConfig

        Raises:
            AnnotationError - if subclass' annotation are not valid
            MissingEnvVarsError - if required environment variables are not set
            ValueError - if environment variables values cannot be parsed into specified type
        """
        cls._validate()
        return cls(**{v.attr: v.value() for v in cls._envvars()})

    @classmethod
    def _validate(cls) -> None:
        """Run validations required to initialize from env vars."""
        not_annotated = [key for key in cls._properties() if key not in cls._annotations()]
        if not_annotated:
            raise AnnotationError(
                "Missing type annotatations in the following properties: "
                + ", ".join(not_annotated)
            )

        missing_envvars = [e.name for e in cls._envvars() if not e.has_value()]
        if missing_envvars:
            raise MissingEnvVarsError(", ".join(missing_envvars))

    @classmethod
    @cache
    def _properties(cls):
        """Get dictionary containg class properties."""
        return {k: v for k, v in cls.__dict__.items() if not k.startswith("__")}

    @classmethod
    def _annotations(cls):
        """Get dictionary containg class properties."""
        if not hasattr(cls, "__annotations__"):
            raise AnnotationError("Subclass must have annotated properties")

        return cls.__annotations__

    @classmethod
    @cache
    def _envvars(cls) -> list[_EnvVar]:
        """Yield over all environment variables."""
        envvars = []
        for key, type_ in cls._annotations().items():
            spec: EnvVar | None = cls._properties().get(key)
            if isinstance(spec, EnvVar):
                envvars.append(
                    _EnvVar(
                        attr=key,
                        name=spec.name or key,
                        default=spec.default,
                        cast=spec.cast or get_caster(type_),
                    )
                )
            elif spec is None:
                envvars.append(
                    _EnvVar(
                        attr=key,
                        name=key,
                        cast=get_caster(type_),
                    )
                )
        return envvars


@dataclass(frozen=True)
class _EnvVar:
    """Environment variable representation."""

    attr: str
    name: str
    cast: EnvVarCaster
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
