"""Host package errors."""


class EnvarifyError(Exception):
    """Base module exception."""


class MissingEnvVarsError(EnvarifyError):
    """Missing environment variables error."""


class AnnotationError(EnvarifyError):
    """Annotation error."""


class UnsupportedTypeError(EnvarifyError):
    """Unsupported type exception."""
