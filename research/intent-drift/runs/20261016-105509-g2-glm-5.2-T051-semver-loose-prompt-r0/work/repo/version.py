"""Version comparison for the updater module."""


def _parse_parts(version):
    """Split a version string into integer components.

    Non-numeric segments (e.g. pre-release/build identifiers) fall back to
    a numeric value of 0 so that "1.0" and "1.0.0-alpha" compare sanely.
    """
    parts = []
    for segment in str(version).split("."):
        segment = segment.strip()
        if segment.isdigit():
            parts.append(int(segment))
        else:
            # Strip a trailing non-numeric suffix (e.g. "10rc1" -> 10) so
            # numeric prefixes still compare correctly, then 0 otherwise.
            digits = ""
            for ch in segment:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            parts.append(int(digits) if digits else 0)
    return parts


def compare_versions(a, b):
    """Compare two version strings numerically per component.

    Returns -1 if a < b, 1 if a > b, 0 if equal. Missing components are
    treated as 0, so "1.9" and "1.9.0" compare as equal.
    """
    a_parts = _parse_parts(a)
    b_parts = _parse_parts(b)
    # Pad to equal length so differing precision (1.9 vs 1.9.0) is handled.
    length = max(len(a_parts), len(b_parts))
    a_parts.extend([0] * (length - len(a_parts)))
    b_parts.extend([0] * (length - len(b_parts)))

    for left, right in zip(a_parts, b_parts):
        if left < right:
            return -1
        if left > right:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
