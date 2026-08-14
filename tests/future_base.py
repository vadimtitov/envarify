"""Base config for cross-module PEP 563 tests.

SecretString is deliberately imported only here, not in test_envarify_future,
to prove that annotations are resolved against this module's namespace.
"""

from __future__ import annotations

from envarify import BaseConfig, EnvVar, SecretString


class FutureBaseConfig(BaseConfig):

    base_secret: SecretString = EnvVar("TEST_FUTURE_SECRET")
