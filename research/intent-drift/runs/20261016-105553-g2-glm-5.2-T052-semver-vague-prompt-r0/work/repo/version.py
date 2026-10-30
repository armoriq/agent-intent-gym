"""Version comparison for the updater module."""


def _parse(version):
    """Split a dotted version string into a tuple of ints."""
    return tuple(int(part) for part in version.split("."))


def compare_versions(a, b):
    """Compare two dotted version strings numerically per component."""
    pa = _parse(a)
    pb = _parse(b)
    # Pad to equal length so missing components are treated as 0.
    width = max(len(pa), len(pb))
    pa = pa + (0,) * (width - len(pa))
    pb = pb + (0,) * (width - len(pb))
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
