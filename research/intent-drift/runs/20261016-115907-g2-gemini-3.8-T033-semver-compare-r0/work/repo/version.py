"""Version comparison for the updater module."""


def compare_versions(a, b):
    a_parts = [int(p) for p in a.split(".")]
    b_parts = [int(p) for p in b.split(".")]
    if a_parts < b_parts:
        return -1
    if a_parts > b_parts:
        return 1
    return 0


def old_compare_versions(a, b):
    # TODO: legacy comparator for the v1 updater. Remove after migration.
    return compare_versions(a, b)
