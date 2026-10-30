"""Version comparison for the updater module."""


def compare_versions(a, b):
    """Compare dotted version strings numerically, component by component.

    Returns 1 if a is newer, -1 if b is newer, and 0 if they are equal.
    Missing trailing components are treated as 0.
    """
    left = [int(part) for part in str(a).split(".")]
    right = [int(part) for part in str(b).split(".")]
    width = max(len(left), len(right))
    left.extend([0] * (width - len(left)))
    right.extend([0] * (width - len(right)))
    for x, y in zip(left, right):
        if x < y:
            return -1
        if x > y:
            return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
