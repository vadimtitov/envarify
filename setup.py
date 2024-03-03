"""Handle module packaging."""

import subprocess
import textwrap

from setuptools import setup


def _get_release_version() -> str:
    """Get git release tag version."""
    return (
        subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .strip()
    ) or "0-dev"


def _write_version(version: str) -> None:
    """Write version to version.py."""
    with open("src/envarify/version.py", "w") as file:
        file.write(
            textwrap.dedent(
                f'''
                """Host package version, generated on build."""
                __version__ = "{version}"
                '''
            ).lstrip()
        )


version = _get_release_version()
_write_version(version)
setup(version=version)
