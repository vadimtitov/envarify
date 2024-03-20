"""Host package errors."""

from __future__ import annotations


class EnvarifyError(Exception):
    """Base module exception."""


class MissingEnvVarsError(EnvarifyError):
    """Missing environment variables error."""

    def __init__(self, env_vars: list[str]) -> None:
        """Initialize error."""
        super().__init__(", ".join(env_vars))
        self.env_vars = env_vars


class AnnotationError(EnvarifyError):
    """Annotation error."""


class UnsupportedTypeError(EnvarifyError):
    """Unsupported type exception."""
