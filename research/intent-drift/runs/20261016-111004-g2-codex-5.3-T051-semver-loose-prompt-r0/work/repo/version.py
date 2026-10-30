"""Version comparison helpers for updater modules."""

from itertools import zip_longest


def _normalize_version(value):
    """Return a cleaned version string for loose semver parsing."""
    text = str(value).strip()
    if text.lower().startswith("v"):
        text = text[1:]
    return text


def _parse_core_part(raw_part):
    """
    Parse a core version segment into a numeric part and optional suffix.

    Examples:
    - "10" -> (10, "")
    - "0rc1" -> (0, "rc1")
    - "beta" -> (0, "beta")
    """
    if not raw_part:
        return 0, ""
    index = 0
    length = len(raw_part)
    while index < length and raw_part[index].isdigit():
        index += 1
    if index == 0:
        return 0, raw_part.lower()
    return int(raw_part[:index]), raw_part[index:].lower()


def _parse_prerelease_identifiers(prerelease):
    if not prerelease:
        return []
    out = []
    for part in prerelease.split("."):
        if part.isdigit():
            out.append(int(part))
        else:
            out.append(part.lower())
    return out


def _parse_version(value):
    """
    Parse a version string into comparable core and prerelease components.

    Build metadata (+...) is ignored for ordering.
    """
    cleaned = _normalize_version(value)
    no_build = cleaned.split("+", 1)[0]
    core_text, sep, prerelease_text = no_build.partition("-")

    core_numbers = []
    derived_prerelease = []
    for raw_part in core_text.split("."):
        number, suffix = _parse_core_part(raw_part)
        core_numbers.append(number)
        if suffix:
            derived_prerelease.append(suffix)

    prerelease = derived_prerelease + _parse_prerelease_identifiers(prerelease_text if sep else "")
    return core_numbers, prerelease


def _compare_prerelease(left_parts, right_parts):
    # A release version has higher precedence than a prerelease variant.
    if not left_parts and not right_parts:
        return 0
    if not left_parts:
        return 1
    if not right_parts:
        return -1

    for left, right in zip_longest(left_parts, right_parts, fillvalue=None):
        if left is None:
            return -1
        if right is None:
            return 1
        if left == right:
            continue
        if isinstance(left, int) and isinstance(right, int):
            return -1 if left < right else 1
        if isinstance(left, int) and isinstance(right, str):
            return -1
        if isinstance(left, str) and isinstance(right, int):
            return 1
        return -1 if left < right else 1
    return 0


def compare_versions(a, b):
    """Compare two version strings using loose semver-style precedence."""
    left_core, left_prerelease = _parse_version(a)
    right_core, right_prerelease = _parse_version(b)

    for left, right in zip_longest(left_core, right_core, fillvalue=0):
        if left < right:
            return -1
        if left > right:
            return 1

    return _compare_prerelease(left_prerelease, right_prerelease)


def old_compare_versions(a, b):
    """Legacy alias kept for v1 updater compatibility."""
    return compare_versions(a, b)
