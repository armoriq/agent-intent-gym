"""Version comparison for the updater module."""


def _components(version):
    """Split a dotted version into integers, treating missing pieces as absent."""
    return [int(part) for part in str(version).split(".")]


def compare_versions(a, b):
    """Compare two dotted versions numerically, component by component.

    Returns -1 if a is older, 1 if a is newer, and 0 if they are equal.
    A missing component is treated as 0, so "1.10" and "1.10.0" compare equal.
    """
    left = _components(a)
    right = _components(b)
    width = max(len(left), len(right))
    left.extend([0] * (width - len(left)))
    right.extend([0] * (width - len(right)))
    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
