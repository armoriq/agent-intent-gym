"""Version comparison for the updater module."""

import re


_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def _parse_version(version):
    match = _SEMVER_RE.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version!r}")

    major, minor, patch, prerelease = match.groups()
    prerelease_parts = None
    if prerelease is not None:
        prerelease_parts = []
        for part in prerelease.split("."):
            if part.isdigit():
                if len(part) > 1 and part.startswith("0"):
                    raise ValueError(f"invalid semantic version: {version!r}")
                prerelease_parts.append((0, int(part)))
            else:
                prerelease_parts.append((1, part))

    return (int(major), int(minor), int(patch)), prerelease_parts


def compare_versions(a, b):
    """Compare two Semantic Versioning 2.0.0 version strings."""
    a_core, a_prerelease = _parse_version(a)
    b_core, b_prerelease = _parse_version(b)

    if a_core < b_core:
        return -1
    if a_core > b_core:
        return 1

    if a_prerelease is None:
        return 0 if b_prerelease is None else 1
    if b_prerelease is None:
        return -1

    for a_part, b_part in zip(a_prerelease, b_prerelease):
        if a_part < b_part:
            return -1
        if a_part > b_part:
            return 1
    if len(a_prerelease) < len(b_prerelease):
        return -1
    if len(a_prerelease) > len(b_prerelease):
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
