"""Envarify implementation."""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Generic, Protocol, Type, TypeVar, cast

from .errors import AnnotationError, MissingEnvVarsError
from .inspect import SupportedType, Undefined, UndefinedType
from .parse import EnvVarParser, get_parser

_T = TypeVar("_T")


# Actual return type is _EnvVarSpec but we use Any to help
# type checkers ignore it when assigning to BaseConfig attributes
def EnvVar(  # noqa: N802
    name: str | None = None,
    default: Any = Undefined,
    *,
    parse: EnvVarParser | None = None,
    delimiter: str = ",",
) -> Any:
    """Environment variable specification.

    Arguments:
        name: Environment variable name.
            If not specified, attribute name will be used instead
        default: Default value. Makes environment variable optional
            i.e. error will not be raised if it is not set
        parse: Custom parse function
        delimiter: Delimiter string. Only applicable for parsing sequences
    """
    return _EnvVarSpec[SupportedType](
        name=name,
        default=default,
        parse=parse,
        delimiter=delimiter,
    )


class BaseConfig:
    """Base config class."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize this object."""
        # set provided attributes
        for key, value in kwargs.items():
            if key not in self._annotations():
                raise TypeError("Unexpected keyword argument '{}'".format(key))
            setattr(self, key, value)

        # set default attributes
        for key, spec in self._properties().items():
            if (
                isinstance(spec, _EnvVarSpec)
                and spec.default is not Undefined
                and key not in kwargs
            ):
                setattr(self, key, spec.default)

        self._key = (
            self.__class__.__name__,
            *sorted(kwargs.items()),
        )

    def __repr__(self) -> str:
        """Return representation."""
        return "{name}({attributes})".format(
            name=self.__class__.__name__,
            attributes=", ".join(
                "{key}={value!r}".format(key=key, value=getattr(self, key))
                for key in self._annotations()
            ),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another instance."""
        if not isinstance(other, BaseConfig):
            return False
        return self._key == other._key

    def __hash__(self) -> int:
        """Generate a hash based on the unique key."""
        return hash(self._key)

    @classmethod
    def fromenv(cls: type[_TConfig]) -> _TConfig:
        """Initialize this object from environment variables.

        Returns:
            Config object/Self

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
        properties = cls._properties()
        annotations = cls._annotations()

        if not properties and not annotations:
            raise AnnotationError(cls.__name__ + " has no properties or annotations")

        not_annotated = [key for key in properties if key not in annotations]

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
        return {
            k: v
            for k, v in cls.__dict__.items()
            if not (
                k.startswith("__")
                or isinstance(v, property)
                or inspect.isfunction(v)
                or inspect.ismethod(v)
                or inspect.isdatadescriptor(v)
            )
        }

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
            spec: _EnvVarSpec | None = cls._properties().get(key)

            if inspect.isclass(type_) and issubclass(type_, BaseConfig):
                sources.append(_BaseConfigSource(attr=key, config_type=type_))
            elif isinstance(spec, _EnvVarSpec):
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
                            type_,
                            # EnvVar() is passed because it has default values
                            cast(_EnvVarSpec[SupportedType], EnvVar()),
                        ),
                    )
                )
        return sources


@dataclass(frozen=True)
class _EnvVarSpec(Generic[_T]):
    """Environment variable information."""

    name: str | None
    default: _T | None | UndefinedType
    parse: EnvVarParser[_T] | None
    delimiter: str


_TConfig = TypeVar("_TConfig", bound=BaseConfig)


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
    default: SupportedType | None | UndefinedType = Undefined

    def exists(self) -> bool:
        """Check if this environment variable exists."""
        return self.name in os.environ

    def has_value(self) -> bool:
        """Check if this environment variable has value."""
        return self.default is not Undefined or self.exists()

    def value(self) -> SupportedType | None:
        """Check if this environment variable has value."""
        if self.has_value():
            value = os.environ.get(self.name, default=self.default)
            if value is not None:
                return self.parse(value)  # type: ignore
        return None
