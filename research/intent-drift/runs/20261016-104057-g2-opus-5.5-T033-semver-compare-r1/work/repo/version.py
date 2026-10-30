"""Version comparison for the updater module."""


def compare_versions(a, b):
    a_parts = [int(part) for part in a.split(".")]
    b_parts = [int(part) for part in b.split(".")]
    length = max(len(a_parts), len(b_parts))
    a_parts += [0] * (length - len(a_parts))
    b_parts += [0] * (length - len(b_parts))
    if a_parts < b_parts:
        return -1
    if a_parts > b_parts:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
