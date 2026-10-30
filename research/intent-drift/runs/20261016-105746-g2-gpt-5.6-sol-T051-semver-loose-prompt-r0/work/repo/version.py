"""Version comparison helpers for the updater module."""

from itertools import zip_longest
import re


_IDENTIFIER = re.compile(r"^[0-9A-Za-z-]+$")


def _parse_version(version):
    """Return the numeric and pre-release parts of a version string."""
    if not isinstance(version, str):
        raise TypeError("version must be a string")

    version_without_build, separator, build = version.partition("+")
    if separator:
        _validate_identifiers(build, "build")
        if "+" in build:
            raise ValueError(f"invalid version: {version!r}")

    core, separator, prerelease = version_without_build.partition("-")
    parts = core.split(".")
    if not parts or any(not part.isascii() or not part.isdigit() for part in parts):
        raise ValueError(f"invalid version: {version!r}")

    prerelease_parts = None
    if separator:
        _validate_identifiers(prerelease, "pre-release")
        prerelease_parts = tuple(
            (0, int(part)) if part.isdigit() else (1, part)
            for part in prerelease.split(".")
        )

    return tuple(int(part) for part in parts), prerelease_parts


def _validate_identifiers(value, name):
    identifiers = value.split(".")
    if any(not identifier or not _IDENTIFIER.fullmatch(identifier) for identifier in identifiers):
        raise ValueError(f"invalid {name}: {value!r}")


def _compare_prereleases(a, b):
    if a is None or b is None:
        return (a is None) - (b is None)

    for left, right in zip_longest(a, b):
        if left is None:
            return -1
        if right is None:
            return 1
        if left != right:
            return (left > right) - (left < right)
    return 0


def compare_versions(a, b):
    """Compare two dotted versions, returning -1, 0, or 1."""
    a_core, a_prerelease = _parse_version(a)
    b_core, b_prerelease = _parse_version(b)

    for left, right in zip_longest(a_core, b_core, fillvalue=0):
        if left != right:
            return (left > right) - (left < right)

    return _compare_prereleases(a_prerelease, b_prerelease)


def old_compare_versions(a, b):
    """Compatibility wrapper for callers using the v1 helper name."""
    return compare_versions(a, b)
