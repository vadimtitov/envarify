"""Envarify implementation."""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol, Type

from .errors import AnnotationError, MissingEnvVarsError
from .parse import EnvVarParser, SupportedType, get_parser


@dataclass(frozen=True)
class EnvVar:
    """Environment variable specification.

    Arguments:
        name: Environment variable name.
            If not specified, attribute name will be used instead
        default: Default value. Makes environment variable optional
            i.e. error will not be raised if it is not set
        parse: Custom parse function
        delimiter: Delimiter string. Only applicable for parsing sequences
    """

    name: str | None = None
    default: str | None = None
    parse: EnvVarParser | None = None
    delimiter: str = ","


class BaseConfig:
    """Base config class."""

    def __init__(self, **kwargs) -> None:
        """Initialize this object."""
        for key, value in kwargs.items():
            if key not in self._annotations():
                raise TypeError("Unexpected keyword argument '{}'".format(key))
            setattr(self, key, value)

    def __repr__(self) -> str:
        """Return representation."""
        return "{name}({attributes})".format(
            name=self.__class__.__name__,
            attributes=", ".join(
                "{key}={value!r}".format(key=key, value=getattr(self, key))
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
        cls.validate()
        return cls(**{v.attr: v.value() for v in cls._sources()})

    @classmethod
    def validate(cls) -> None:
        """Run validations required to initialize from env vars."""
        not_annotated = [key for key in cls._properties() if key not in cls._annotations()]
        if not_annotated:
            raise AnnotationError(
                "Missing type annotatations in the following properties: "
                + ", ".join(not_annotated)
            )

        # collect from this config class
        missing_envvars = [e.name for e in cls._envvars() if not e.has_value()]

        # collect from child config classes
        for base_class in cls._base_classes():
            try:
                base_class.config_type.validate()
            except MissingEnvVarsError as e:
                missing_envvars.extend(e.env_vars)

        if missing_envvars:
            raise MissingEnvVarsError(missing_envvars)

    @classmethod
    @lru_cache
    def _properties(cls) -> dict[str, Any]:
        """Get dictionary containg class properties."""
        return {k: v for k, v in cls.__dict__.items() if not k.startswith("__")}

    @classmethod
    def _annotations(cls) -> dict[str, Type]:
        """Get dictionary containg class properties."""
        if not hasattr(cls, "__annotations__"):
            raise AnnotationError("Subclass must have annotated properties")

        return cls.__annotations__

    @classmethod
    @lru_cache
    def _envvars(cls) -> list[_EnvVarSource]:
        """Yield over all environment variables."""
        return [source for source in cls._sources() if isinstance(source, _EnvVarSource)]

    @classmethod
    @lru_cache
    def _base_classes(cls) -> list[_BaseConfigSource]:
        """Yield over all base config sources."""
        return [source for source in cls._sources() if isinstance(source, _BaseConfigSource)]

    @classmethod
    @lru_cache
    def _sources(cls) -> list[_ValueSource]:
        """Yield over all value sources."""
        sources: list[_ValueSource] = []

        for key, type_ in cls._annotations().items():
            spec: EnvVar | None = cls._properties().get(key)

            if inspect.isclass(type_) and issubclass(type_, BaseConfig):
                sources.append(_BaseConfigSource(attr=key, config_type=type_))
            elif isinstance(spec, EnvVar):
                sources.append(
                    _EnvVarSource(
                        attr=key,
                        name=spec.name or key,
                        default=spec.default,
                        parse=spec.parse or get_parser(type_, spec),
                    )
                )
            elif spec is None:
                sources.append(
                    _EnvVarSource(
                        attr=key,
                        name=key,
                        parse=get_parser(
                            type_, EnvVar()  # EnvVar() is passed because it has default values
                        ),
                    )
                )
        return sources


class _ValueSource(Protocol):

    attr: str

    def value(self) -> SupportedType | BaseConfig | None: ...


@dataclass(frozen=True)
class _BaseConfigSource(_ValueSource):
    """Base config source."""

    attr: str
    config_type: Type[BaseConfig]

    def value(self) -> BaseConfig:
        return self.config_type.fromenv()


@dataclass(frozen=True)
class _EnvVarSource(_ValueSource):
    """Environment variable representation."""

    attr: str
    name: str
    parse: EnvVarParser
    default: str | None = None

    def exists(self) -> bool:
        """Check if this environment variable exists."""
        return self.name in os.environ

    def has_value(self) -> bool:
        """Check if this environment variable has value."""
        return self.default is not None or self.exists()

    def value(self) -> SupportedType | None:
        """Check if this environment variable has value."""
        if self.has_value():
            value = os.environ.get(self.name, default=self.default)
            return self.parse(value)  # type: ignore
        return None
