"""Version comparison for the updater module."""
from itertools import zip_longest


def _parse(version):
    return [int(part) for part in version.split(".")]


def compare_versions(a, b):
    """Return -1, 0 or 1 as version string a is older, equal or newer than b.

    Missing trailing components count as zero, so "1.2" == "1.2.0".
    """
    for x, y in zip_longest(_parse(a), _parse(b), fillvalue=0):
        if x != y:
            return -1 if x < y else 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
